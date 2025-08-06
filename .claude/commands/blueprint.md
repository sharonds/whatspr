# /blueprint

**CONTEXT INITIALIZATION:** This command starts a new feature workflow session.

What feature do you want to build?

# /blueprint

**CONTEXT INITIALIZATION:** This command starts a new MVP feature workflow session.

What feature do you want to build?

**Step 1: Load Project Context**
@blueprint-specialist Read `CLAUDE.md` for project context, then create an MVP-focused TDD plan for this feature: [USER_INPUT]

**MVP Planning Focus:**
- Essential functionality only (defer nice-to-haves)
- Core test scenarios (avoid edge case over-testing)
- Direct production deployment (no staging complexity)
- Minimal viable implementation

**Required Output:**
1. Git branch name (feat/xxx format)
2. Essential failing test suite (core scenarios only)
3. Minimal file structure recommendations
4. Direct production deployment notes
5. MVP success criteria

**Fallback:** If @blueprint-specialist unavailable, provide MVP TDD planning focusing on essential functionality and core tests only.

Don't write implementation code - only essential tests and lean MVP plan.

**Required Output:**
1. Git branch name (feat/xxx format)
2. Comprehensive failing test suite covering all scenarios
3. File structure recommendations
4. Deployment complexity assessment (Simple/Complex)
5. Implementation strategy

**Context Tracking:** After this command, remember the feature name and key details for all subsequent workflow steps.

**Fallback:** If @blueprint-specialist is not available, provide TDD planning with the same expert criteria: comprehensive failing tests, staging considerations, and implementation strategy.

Don't write implementation code - only tests and plans.
