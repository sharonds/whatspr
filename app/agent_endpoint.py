"""WhatsApp webhook endpoints for AI agent conversation handling.

Provides FastAPI routes for processing WhatsApp messages through AI agent,
managing conversation sessions, and dispatching tool calls with timeout protection.
"""

import asyncio
import time
import random
from fastapi import APIRouter, Request
from .agent_runtime import run_thread, ATOMIC_FUNCS
from .prefilter import clean_message, twiml
from .validator_tool import validate_local
from . import tools_atomic as tools
from .session_manager import SessionManager
from .session_config.session_config import SessionConfig
from .timeout_config import timeout_manager
import structlog
from typing import Dict, Optional, Tuple, List

router = APIRouter()
log = structlog.get_logger("agent")

# Feature flag for session manager rollout
USE_SESSION_MANAGER = True  # Set to False to use legacy _sessions dict

_sessions: Dict[str, Optional[str]] = {}  # phone -> thread_id (None until first message)

# Initialize session manager
session_manager = SessionManager(SessionConfig())


# Timeout configuration now centralized through timeout_manager
# These getter functions provide backward compatibility and centralized config access
def get_max_ai_processing_time() -> float:
    """Get maximum AI processing time from centralized config."""
    return timeout_manager.config.ai_processing_timeout


def get_max_retries() -> int:
    """Get maximum retry attempts from centralized config."""
    return timeout_manager.config.retry_max_attempts


def get_retry_base_delay() -> float:
    """Get retry base delay from centralized config."""
    return timeout_manager.config.retry_base_delay


def get_retry_max_delay() -> float:
    """Get retry maximum delay from centralized config."""
    return timeout_manager.config.retry_max_delay


async def run_single_attempt(
    thread_id: Optional[str], user_msg: str, timeout_seconds: float
) -> Tuple[str, str, List[dict]]:
    """Run a single AI processing attempt with timeout.

    Args:
        thread_id: Optional thread ID for conversation continuation.
        user_msg: User message to process.
        timeout_seconds: Maximum time to wait for response.

    Returns:
        Tuple of (reply, thread_id, tool_calls).

    Raises:
        asyncio.TimeoutError: If the operation times out.
        Exception: If the operation fails for other reasons.
    """
    loop = asyncio.get_event_loop()
    task = loop.run_in_executor(None, run_thread, thread_id, user_msg)
    return await asyncio.wait_for(task, timeout=timeout_seconds)


async def run_thread_with_retry(
    thread_id: Optional[str], user_msg: str, timeout_seconds: float = None
) -> Tuple[str, str, List[dict]]:
    """Run thread with retry logic and timeout protection.

    Args:
        thread_id: Optional thread ID for conversation continuation.
        user_msg: User message to process.
        timeout_seconds: Maximum time to wait for response. If None, uses default from config.

    Returns:
        Tuple of (reply, thread_id, tool_calls) or fallback response on failure.
    """
    # Use centralized timeout configuration
    if timeout_seconds is None:
        timeout_seconds = get_max_ai_processing_time()

    start_time = time.time()
    last_exception = None
    max_retries = get_max_retries()

    # Calculate per-attempt timeout (reserve time for retries)
    per_attempt_timeout = timeout_seconds / (max_retries + 1)

    for attempt in range(max_retries + 1):
        try:
            # Adjust timeout for remaining time
            remaining_time = timeout_seconds - (time.time() - start_time)
            attempt_timeout = min(per_attempt_timeout, remaining_time - 0.5)  # Leave 0.5s buffer

            if attempt_timeout <= 0:
                log.warning(
                    "insufficient_time_for_retry", attempt=attempt, remaining_time=remaining_time
                )
                break

            log.info(
                "ai_attempt_start",
                attempt=attempt + 1,
                max_attempts=max_retries + 1,
                attempt_timeout=attempt_timeout,
            )

            reply, thread_id, tool_calls = await run_single_attempt(
                thread_id, user_msg, attempt_timeout
            )

            elapsed = time.time() - start_time
            log.info(
                "ai_success",
                attempt=attempt + 1,
                elapsed_seconds=elapsed,
                timeout_seconds=timeout_seconds,
            )

            return reply, thread_id, tool_calls

        except asyncio.TimeoutError as e:
            last_exception = e
            elapsed = time.time() - start_time
            log.warning(
                "ai_attempt_timeout",
                attempt=attempt + 1,
                elapsed_seconds=elapsed,
                attempt_timeout=attempt_timeout,
            )

        except Exception as e:
            last_exception = e
            elapsed = time.time() - start_time
            log.warning(
                "ai_attempt_error",
                attempt=attempt + 1,
                error=str(e),
                error_type=type(e).__name__,
                elapsed_seconds=elapsed,
                # Enhanced error details for OpenAI-specific issues
                error_details=getattr(e, 'response', {}) if hasattr(e, 'response') else {},
                openai_error_code=getattr(e, 'code', None) if hasattr(e, 'code') else None,
            )

        # Don't retry on the last attempt
        if attempt < max_retries:
            # Calculate exponential backoff delay with jitter
            delay = min(
                get_retry_base_delay() * (2**attempt) + random.uniform(0, 0.1),
                get_retry_max_delay(),
            )

            # Check if we have time for delay + another attempt
            remaining_time = timeout_seconds - (time.time() - start_time)
            if remaining_time > delay + 1.0:  # Need at least 1s for next attempt
                log.info("ai_retry_delay", delay=delay, remaining_time=remaining_time)
                await asyncio.sleep(delay)
            else:
                log.warning("insufficient_time_for_delay", remaining_time=remaining_time)
                break

    # All attempts failed - handle gracefully
    elapsed = time.time() - start_time

    # Enhanced error logging with more details
    error_summary = str(last_exception) if last_exception else "Unknown error"
    error_type = type(last_exception).__name__ if last_exception else "Unknown"

    log.error(
        "ai_all_attempts_failed",
        attempts=max_retries + 1,
        elapsed_seconds=elapsed,
        final_error=error_summary,
        final_error_type=error_type,
        user_msg=user_msg[:100],
        # Additional debugging info
        timeout_seconds=timeout_seconds,
        per_attempt_timeout=timeout_seconds / (max_retries + 1),
    )

    # Create thread if needed but preserve existing thread_id on failure
    if thread_id is None:
        from .agent_runtime import create_thread

        thread_id = create_thread()
        log.info("thread_created_after_failure", thread_id=thread_id)

    # Return appropriate fallback based on the type of failure
    if isinstance(last_exception, asyncio.TimeoutError):
        fallback_reply = (
            "I'm processing your request. Please give me a moment and try again shortly."
        )
    else:
        fallback_reply = "I'm having trouble processing your request right now. Please try again."

    return fallback_reply, thread_id, []


# Tool dispatch table for cleaner handling
def save_slot_fn(name: str, value: str) -> dict:
    """Save slot value with logging (placeholder implementation).

    Args:
        name: Slot name to save.
        value: Value to save for the slot.

    Returns:
        dict: Status response with saved slot information.
    """
    log.info("save_slot", name=name, value=value)
    return {"status": "saved", "name": name, "value": value}


def get_slot_fn(name: str) -> dict:
    """Retrieve slot value with logging (placeholder implementation).

    Args:
        name: Slot name to retrieve.

    Returns:
        dict: Slot information with empty value (placeholder).
    """
    log.info("get_slot", name=name)
    return {"value": "", "name": name}


def finish_fn() -> dict:
    """Mark conversation as finished with logging.

    Returns:
        dict: Completion status response.
    """
    log.info("finish")
    return {"status": "finished"}


TOOL_DISPATCH = {
    "save_slot": save_slot_fn,
    "get_slot": get_slot_fn,
    "validate_local": validate_local,
    "finish": finish_fn,
    **{fn: getattr(tools, fn) for fn in ATOMIC_FUNCS},
}


@router.post("/agent")
async def agent_hook(request: Request):
    """Main agent endpoint for processing WhatsApp messages.

    Handles incoming WhatsApp messages through AI agent conversation flow.
    Manages session state, processes reset commands, and executes tool calls.

    Args:
        request: FastAPI request containing WhatsApp webhook data.

    Returns:
        Response: TwiML response with agent's reply message.
    """
    form = await request.form()
    phone = str(form.get("From", ""))
    body = str(form.get("Body", ""))
    clean = clean_message(body)
    if clean is None:
        return twiml("Please send text.")

    # Handle reset commands
    if clean.lower() in ["reset", "restart", "start over", "menu", "start"]:
        log.info("session_reset", phone_hash=phone[-4:] if phone else "none")
        # Clear session, thread will be created lazily when needed
        if USE_SESSION_MANAGER:
            session_manager.remove_session(phone)
        else:
            _sessions[phone] = None
        return twiml(
            "👋 Hi! What kind of announcement?\n  Press 1 for Funding round\n  Press 2 for Product launch\n  Press 3 for Partnership / integration"
        )

    # Get thread_id (may be None for new sessions)
    if USE_SESSION_MANAGER:
        thread_id = session_manager.get_session(phone)
    else:
        thread_id = _sessions.get(phone)

    # Pre-process numeric menu selections
    if clean.strip() in ["1", "1️⃣"]:
        clean = "I want to announce a funding round"
    elif clean.strip() in ["2", "2️⃣"]:
        clean = "I want to announce a product launch"
    elif clean.strip() in ["3", "3️⃣"]:
        clean = "I want to announce a partnership or integration"

    try:
        request_start_time = time.time()
        log.info(
            "debug_request",
            phone_hash=phone[-4:] if phone else "none",
            body_length=len(clean),
        )

        # Use retry-enabled AI processing with timeout protection
        reply, thread_id, tool_calls = await run_thread_with_retry(thread_id, clean)

        # Only update session if we have a valid thread_id
        if thread_id and thread_id.strip():
            if USE_SESSION_MANAGER:
                session_manager.set_session(phone, thread_id)
            else:
                _sessions[phone] = thread_id
        else:
            log.error(
                "invalid_thread_id_returned",
                thread_id=repr(thread_id),
                phone_hash=phone[-4:] if phone else "none",
            )

        processing_time = time.time() - request_start_time
        log.info(
            "debug_response",
            reply_length=len(reply),
            tool_count=len(tool_calls),
            total_time=processing_time,
        )

        # Handle tool calls using dispatch table
        for call in tool_calls:
            call_dict = dict(call)  # Ensure proper dict type for type checker
            if call_dict.get("name") in TOOL_DISPATCH:
                TOOL_DISPATCH[call_dict["name"]](**call_dict.get("arguments", {}))
                log.info("tool_executed", name=call_dict["name"])
            else:
                log.warning("unknown_tool", name=call_dict.get("name", "unknown"))

    except Exception as e:
        log.error("agent_error", error=str(e), error_type=type(e).__name__, exc_info=True)
        return twiml("Oops, temporary error. Try again.")
    return twiml(reply)


@router.post("/whatsapp")
async def whatsapp_hook(request: Request):
    """Primary WhatsApp webhook endpoint for agent mode.

    Routes WhatsApp webhook requests to the agent conversation handler
    when agent mode is enabled as the default processing mode.

    Args:
        request: FastAPI request containing WhatsApp webhook data.

    Returns:
        Response: TwiML response from agent_hook.
    """
    return await agent_hook(request)
