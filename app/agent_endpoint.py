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
        # Enhanced reset logging for MVP user tracking
        if USE_SESSION_MANAGER:
            existing_session = session_manager.get_session(phone)
            session_manager.remove_session(phone)
            log.info(
                "session_reset_requested",
                phone_hash=phone[-4:] if phone else "none",
                had_existing_session=existing_session is not None,
                existing_thread_prefix=existing_session[:10] if existing_session else None,
                reset_command=clean.lower(),
                total_active_sessions=session_manager.get_session_count(),
            )
        else:
            existing_thread = _sessions.get(phone)
            _sessions[phone] = None
            log.info(
                "session_reset_requested_legacy",
                phone_hash=phone[-4:] if phone else "none",
                had_existing_session=existing_thread is not None,
                reset_command=clean.lower(),
            )
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

        # Enhanced conversation flow logging for MVP user tracking
        conversation_context = {
            "phone_hash": phone[-4:] if phone else "none",
            "message_length": len(clean),
            "has_existing_session": thread_id is not None,
            "existing_thread_prefix": thread_id[:10] if thread_id else None,
            "is_menu_selection": clean.strip() in ["1", "1️⃣", "2", "2️⃣", "3", "3️⃣"],
            "message_preview": clean[:50] + "..." if len(clean) > 50 else clean,
        }

        if USE_SESSION_MANAGER:
            conversation_context["total_active_sessions"] = session_manager.get_session_count()

        log.info("conversation_message_received", **conversation_context)

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

        # Enhanced response logging with conversation flow insights
        response_context = {
            "reply_length": len(reply),
            "tool_count": len(tool_calls),
            "processing_time_seconds": round(processing_time, 3),
            "phone_hash": phone[-4:] if phone else "none",
            "thread_id_prefix": thread_id[:10] if thread_id else None,
            "reply_preview": reply[:100] + "..." if len(reply) > 100 else reply,
        }

        if USE_SESSION_MANAGER:
            response_context["total_active_sessions_after"] = session_manager.get_session_count()

        # Add tool call details for press release flow tracking
        if tool_calls:
            tool_names = [call.get("name", "unknown") for call in tool_calls]
            response_context["tools_called"] = tool_names

            # Track press release progress
            atomic_tools_used = [name for name in tool_names if name in ATOMIC_FUNCS]
            if atomic_tools_used:
                response_context["pr_tools_used"] = atomic_tools_used

        log.info("conversation_message_processed", **response_context)

        # Handle tool calls using dispatch table with enhanced logging
        for call in tool_calls:
            call_dict = dict(call)  # Ensure proper dict type for type checker
            tool_name = call_dict.get("name", "unknown")

            if tool_name in TOOL_DISPATCH:
                try:
                    tool_result = TOOL_DISPATCH[tool_name](**call_dict.get("arguments", {}))

                    # Enhanced tool execution logging for MVP press release flow tracking
                    log.info(
                        "tool_executed_success",
                        tool_name=tool_name,
                        phone_hash=phone[-4:] if phone else "none",
                        thread_id_prefix=thread_id[:10] if thread_id else None,
                        is_atomic_tool=tool_name in ATOMIC_FUNCS,
                        tool_arguments_count=len(call_dict.get("arguments", {})),
                    )

                    # Track press release completion progress
                    if tool_name in ATOMIC_FUNCS:
                        log.info(
                            "pr_data_saved",
                            data_type=tool_name,
                            phone_hash=phone[-4:] if phone else "none",
                            thread_id_prefix=thread_id[:10] if thread_id else None,
                        )
                    elif tool_name == "finish":
                        log.info(
                            "pr_completion",
                            phone_hash=phone[-4:] if phone else "none",
                            thread_id_prefix=thread_id[:10] if thread_id else None,
                            total_tools_used=len(tool_calls),
                        )

                except Exception as tool_error:
                    log.error(
                        "tool_execution_failed",
                        tool_name=tool_name,
                        phone_hash=phone[-4:] if phone else "none",
                        error=str(tool_error),
                        error_type=type(tool_error).__name__,
                    )
            else:
                log.warning(
                    "unknown_tool_called",
                    tool_name=tool_name,
                    phone_hash=phone[-4:] if phone else "none",
                    available_tools=list(TOOL_DISPATCH.keys())[:5],  # First 5 for log size
                )

    except Exception as e:
        # Enhanced error logging for MVP debugging
        log.error(
            "conversation_processing_failed",
            error=str(e),
            error_type=type(e).__name__,
            phone_hash=phone[-4:] if phone else "none",
            message_preview=clean[:50] if clean else "none",
            had_session=thread_id is not None,
            processing_time=(
                round(time.time() - request_start_time, 3)
                if 'request_start_time' in locals()
                else None
            ),
            exc_info=True,
        )
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


@router.get("/health/sessions")
async def sessions_health():
    """Session monitoring endpoint for MVP health checks.

    Provides basic session metrics and health information for monitoring
    the SessionManager during MVP deployment with real users.

    Returns:
        dict: Session health metrics and status information.
    """
    if USE_SESSION_MANAGER:
        metrics = session_manager.get_metrics()

        # Add health indicators
        health_status = "healthy"
        warnings = []

        # Check for potential issues
        if metrics['active_sessions'] > 50:  # High for MVP
            warnings.append("High session count for MVP deployment")
            health_status = "warning"

        if metrics['estimated_memory_bytes'] > 100000:  # 100KB threshold
            warnings.append("High memory usage for session storage")
            health_status = "warning"

        return {
            "status": health_status,
            "session_manager": {"enabled": True, "metrics": metrics, "warnings": warnings},
            "timestamp": time.time(),
        }
    else:
        # Legacy mode metrics
        active_legacy_sessions = len([v for v in _sessions.values() if v is not None])
        return {
            "status": "legacy",
            "session_manager": {
                "enabled": False,
                "legacy_active_sessions": active_legacy_sessions,
                "legacy_total_entries": len(_sessions),
            },
            "timestamp": time.time(),
        }


@router.get("/health/sessions/details")
async def sessions_details():
    """Detailed session information for debugging (MVP safe).

    Provides detailed session information while protecting user privacy
    by hashing phone numbers and showing only last 4 characters.

    Returns:
        dict: Detailed session information for debugging.
    """
    if not USE_SESSION_MANAGER:
        return {"error": "Session manager not enabled", "status": "legacy"}

    # Get metrics and add computed values
    metrics = session_manager.get_metrics()

    # Calculate session age distribution (approximate)
    current_time = time.time()
    session_details = []

    for phone, entry in session_manager._sessions.items():
        # Protect privacy with phone hash
        phone_hash = phone[-4:] if len(phone) >= 4 else "****"

        created_ago = (current_time - entry.created_at.timestamp()) / 60  # minutes
        accessed_ago = (current_time - entry.last_accessed.timestamp()) / 60  # minutes

        session_details.append(
            {
                "phone_hash": phone_hash,
                "thread_id_prefix": (
                    entry.thread_id[:10] + "..." if len(entry.thread_id) > 10 else entry.thread_id
                ),
                "created_minutes_ago": round(created_ago, 1),
                "last_accessed_minutes_ago": round(accessed_ago, 1),
                "is_near_expiry": accessed_ago
                > (session_manager.config.ttl_seconds / 60) * 0.8,  # 80% of TTL
            }
        )

    # Sort by most recently accessed
    session_details.sort(key=lambda x: x["last_accessed_minutes_ago"])

    return {
        "overview": metrics,
        "config": {
            "ttl_minutes": session_manager.config.ttl_seconds / 60,
            "cleanup_interval_seconds": session_manager.config.cleanup_interval,
        },
        "sessions": session_details[:20],  # Limit to 20 most recent for MVP
        "total_sessions_shown": min(len(session_details), 20),
        "timestamp": current_time,
    }


@router.post("/health/sessions/cleanup")
async def force_session_cleanup():
    """Force session cleanup for MVP monitoring and debugging.

    Manually triggers session cleanup and returns results.
    Useful for testing cleanup behavior during MVP deployment.

    Returns:
        dict: Cleanup results and updated metrics.
    """
    if not USE_SESSION_MANAGER:
        return {"error": "Session manager not enabled", "status": "legacy"}

    # Capture before state
    before_metrics = session_manager.get_metrics()

    # Run cleanup
    cleanup_start = time.time()
    removed_count = session_manager.cleanup_expired_sessions()
    cleanup_duration = time.time() - cleanup_start

    # Capture after state
    after_metrics = session_manager.get_metrics()

    return {
        "cleanup_results": {
            "removed_sessions": removed_count,
            "cleanup_duration_ms": round(cleanup_duration * 1000, 2),
            "before_active_sessions": before_metrics['active_sessions'],
            "after_active_sessions": after_metrics['active_sessions'],
        },
        "metrics_change": {
            "sessions_delta": after_metrics['active_sessions'] - before_metrics['active_sessions'],
            "memory_delta_bytes": after_metrics['estimated_memory_bytes']
            - before_metrics['estimated_memory_bytes'],
        },
        "current_metrics": after_metrics,
        "timestamp": time.time(),
    }
