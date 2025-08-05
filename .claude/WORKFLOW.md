# Claude Code Context-Aware Workflow

## Commands (Context-Aware)
- `/blueprint` - Prompts for feature idea, remembers for session
- `/qa-review` - Reviews the feature from blueprint
- `/update-docs` - Documents the feature from blueprint  
- `/review-commits` - Organizes commits for current feature
- `/create-pr` - Creates PR for current feature

## Usage Flow (Single Session)
```bash
# Start Claude Code session
claude

# 1. Plan (Sets context for entire session)
/blueprint
# Responds to: "What feature do you want to build?"
# Example: "Add JWT authentication with login/logout"

# 2. Build (follow TDD cycle)
# Implement until tests pass

# 3. Quality Review (Knows you're working on JWT auth)
/qa-review
# No need to re-explain - Claude remembers the feature

# 4. Update Documentation (Still knows the feature)
/update-docs
# Updates docs for JWT auth feature automatically

# 5. Organize Commits (Context-aware)
git add .
/review-commits
# Organizes JWT auth commits

# 6. Create PR (Remembers everything)
/create-pr
# Generates PR for JWT auth feature
```

## Key Benefits
- **Session Memory**: Commands remember feature from `/blueprint`
- **No Repetition**: Don't re-explain feature in each command
- **Natural Flow**: Conversational workflow within single session
- **Focus**: Each command focuses on its specific task
- **Professional**: Still follows conventional commit and PR standards

## Tips
- Always start with `/blueprint` to set session context
- Work through commands in order for best results
- Complete feature in single Claude session for full context
- Commands will reference "the feature we've been working on"
