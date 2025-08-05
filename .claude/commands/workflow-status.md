# /workflow-status

**Workflow Progress Check**

Analyze current project state and determine workflow progress:

**Auto-Detection:**
1. **Current Feature:** [From git branch name or recent commits]
2. **Completed Steps:** 
   - ✅ Blueprint: [Check for test files created]
   - ✅ Implementation: [Check if tests passing]
   - ✅ QA Review: [Check for review comments/fixes]
   - ✅ Staging Prep: [Check for deployment configs]
   - ✅ Documentation: [Check doc updates]
   - ✅ Commits: [Check commit history]
   - ✅ PR: [Check for PR creation]

**Next Recommended Action:**
Based on current state, suggest the next workflow command to run.

**Context for Next Step:**
Provide the context summary needed for the next workflow command.
