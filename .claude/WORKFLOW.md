# Claude Code MVP Workflow with Sub-Agents

## ⚠️ **Why This MVP Workflow is Essential**

**Claude Code's Default Behavior** will bypass your quality gates! Without custom slash commands:

❌ **Implements features completely**  
❌ **Commits changes automatically**  
❌ **Creates PRs without review**  
❌ **Skips QA and documentation**

**Your MVP workflow prevents this by enforcing controlled execution.**

## 🚀 Streamlined 5-Step MVP Workflow

1. **`/blueprint`** - @blueprint-specialist: MVP TDD planning + context init
2. **Build** - Follow TDD cycle focusing on core functionality  
3. **`/qa-review`** - @qa-specialist: Essential quality & security review
4. **`/update-docs`** - @documentation-specialist: Essential documentation
5. **`/review-commits`** - @git-specialist: Clean commit organization
6. **`/create-pr`** - @pr-specialist: Streamlined PR documentation

## Strategic Planning
- **`/strategic-planning`** - @strategic-planner: MVP priority assessment (every 2-3 features)

## Support Commands
- **`/context-sync`** - Synchronize MVP development context
- **`/workflow-status`** - Check MVP progress and next steps

## MVP Sub-Agent Specialists
- **blueprint-specialist** - MVP TDD planning with essential functionality focus
- **qa-specialist** - Critical security and production safety expert
- **documentation-specialist** - Essential documentation and deployment notes
- **git-specialist** - Clean, deployable commit organization
- **pr-specialist** - Production-focused PR documentation
- **strategic-planner** - MVP prioritization and user value assessment

## MVP Philosophy
- **Ship core functionality quickly**
- **Essential quality gates only** 
- **Direct production deployment**
- **Iterate based on user feedback**
- **Perfect later, ship now**

## Real MVP Usage Example

```bash
# Start MVP session
claude

# 1. MVP Planning
/blueprint
# You: "Add user login with email/password"
# Result: Focused plan with essential login tests only

# 2. Build Core Feature
# Implement following MVP plan - core login functionality only

# 3. Essential QA
/qa-review
# Feature: User login, Files: auth.js, login.jsx, api/auth.js
# Result: Security issues and basic functionality check

# 4. Essential Docs
/update-docs
# Result: Updates CLAUDE.md and environment variables

# 5. Clean Commits  
git add .
/review-commits
# Result: Clean, deployable commits

# 6. Production PR
/create-pr
# Result: Focused PR for production deployment
```

## ✅ MVP Benefits

| MVP Advantage | Benefit |
|---------------|---------|
| **Speed** | 3-4 min overhead for professional development |
| **Focus** | Core functionality over perfect infrastructure |
| **Deployment** | Direct to production, faster feedback |
| **Iteration** | Ship, learn, improve cycle |
| **Quality** | Essential gates without over-engineering |

**Perfect for:** Early-stage products, rapid prototyping, user validation, lean teams.

---

*This MVP-optimized workflow maximizes development velocity while maintaining essential quality gates for production deployment.*
