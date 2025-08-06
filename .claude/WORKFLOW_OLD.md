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

## Context Management Protocol

### Starting New Feature:
```bash
/blueprint  # Initializes context for entire workflow
```

### During Workflow:
```bash
/context-sync  # If context seems unclear between steps
/workflow-status  # Check progress and get next step
```

### Context Passing Format:
```markdown
Feature Name: [CLEAR_NAME]
Implementation: [BRIEF_SUMMARY]
```

## Error Handling

### Sub-Agent Unavailable:
Each command includes fallback instructions to continue with main Claude using the same expert criteria.

### Context Lost:
```bash
/context-sync  # Reconstructs context from project state
/workflow-status  # Determines current position in workflow
```

### Workflow Interruption:
```bash
/workflow-status  # Determines where to resume
# Continue from recommended next step
```

## Usage Flow (Single Session with Expert Sub-Agents)

```bash
# Complete professional development cycle:
claude
/blueprint          # Expert TDD planning + context init
# [Implement following TDD cycle]
/qa-review          # Expert security/quality review  
/staging-deploy     # Expert deployment preparation
/update-docs        # Expert documentation updates
/review-commits     # Expert git organization
git add .
# [Execute provided git commands]
/create-pr          # Expert PR documentation
```

**Total Time:** ~4-5 minutes overhead for enterprise-grade professional development cycle

## Best Practices

### Context Management:
- Always specify feature name when switching between steps
- Use `/context-sync` if any confusion about current state
- Include brief implementation summary in later steps

### Sub-Agent Usage:
- Trust sub-agent expertise in their domains
- Provide explicit context in each command
- Use fallback instructions if sub-agents unavailable

### Error Recovery:
- `/workflow-status` to understand current position
- Restart Claude Code session if sub-agents not responding
- Continue with main Claude using sub-agent criteria as fallback

## Troubleshooting

### Sub-Agents Not Invoking:
1. Check `/agents` command to verify sub-agent availability
2. Restart Claude Code session
3. Use fallback instructions in commands

### Context Confusion:
1. Run `/context-sync` to clarify current state
2. Explicitly provide feature name and brief summary
3. Use `/workflow-status` to determine next step

### Workflow Interruption:
1. Run `/workflow-status` to assess current position
2. Continue from recommended next step
3. Use context from status command for subsequent steps

## WhatsApp PR Agent Specific Usage

Given your current project context with atomic tools and goal-oriented prompts, here's how to apply this workflow:

### Example: Adding E2E Testing Enhancement
```bash
claude
/blueprint
# Feature: "Add comprehensive E2E testing for difficult conversation inputs"

# After implementing:
/qa-review
# Feature Name: E2E Testing Enhancement
# Key Implementation: Added comprehensive conversation flow tests with edge cases

/staging-deploy  
# Feature Name: E2E Testing Enhancement
# Implementation Summary: New E2E tests with difficult input scenarios

/update-docs
# Feature Name: E2E Testing Enhancement
# Key Changes: New testing procedures, staging validation steps

/review-commits
# Feature Name: E2E Testing Enhancement
# Scope: Test files, documentation, staging scripts

/create-pr
# Feature Name: E2E Testing Enhancement
# Implementation: Comprehensive E2E testing framework for conversation flows
```

## Benefits for WhatsApp PR Agent Project

- **Quality Gates**: Prevents bypassing QA, staging, and documentation steps
- **Expert Review**: Each phase reviewed by specialized sub-agent
- **Context Continuity**: Feature context maintained throughout workflow
- **Atomic Commits**: Clean git history with logical commit organization
- **Professional PRs**: Consistent, reviewer-focused PR documentation
- **Error Recovery**: Graceful handling of workflow interruptions
