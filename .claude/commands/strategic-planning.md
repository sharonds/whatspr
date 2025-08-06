# /strategic-planning

**APP OBJECTIVE:** [Specify your MVP goals and target user value]

**CURRENT MVP STATUS:**
- Recent features completed: [Last 2-3 features]
- Known issues/blockers: [Current problems]  
- User feedback: [Key insights if available]

@strategic-planner Read `CLAUDE.md` current status, then analyze and recommend next MVP priorities.

**MVP Strategic Analysis:**
1. **User Value Assessment** - Features directly impacting user experience
2. **Technical Risk Review** - Issues that could break production
3. **Development Velocity** - Blockers slowing feature delivery
4. **Market Validation** - What's needed for user feedback

**MVP Prioritization Framework:**
- **Ship-Blockers** - Critical bugs, security issues (fix immediately)
- **Core Value** - Direct user benefit features (next iteration)
- **Foundation** - Technical improvements for faster development
- **Nice-to-Haves** - Defer until post-MVP

**Required Output:**
```markdown
## Next MVP Priorities

### Ship-Blockers (Immediate)
1. [Critical issue] - Impact + effort estimate

### Core Features (Next 1-2 weeks)  
1. [User value feature] - Benefit + effort estimate

### Foundation (After core features)
1. [Technical improvement] - Velocity gain + effort

## Next Sprint Plan
**This week:** [Top 2-3 priorities with reasoning]
**Next week:** [Following 2-3 priorities]
```

**MVP Focus:** Ship working features, get user feedback, iterate quickly.

**Fallback:** If @strategic-planner unavailable, prioritize user-facing features and production stability over internal improvements.
