# CLAUDE.md - MVP Project Context

*Last Updated: [DATE] | MVP Status: [Phase - e.g., Core Features/User Validation/Growth]*

## 🎯 MVP Overview

### **Core Value Proposition**
[What problem does your MVP solve in one clear sentence?]

### **Target Users**
[Primary user type and their main use case - keep focused]

### **MVP Success Criteria**
- **User Adoption:** [Specific metric - e.g., 100 active users]
- **Core Functionality:** [Key features that must work]
- **Technical Stability:** [Uptime/performance minimums]

---

## 🏗️ Technical Foundation

### **Technology Stack**
- **Frontend:** [Framework + key libraries]
- **Backend:** [Framework + database]
- **Deployment:** [Platform - e.g., Vercel, Railway, Render]
- **External Services:** [Critical integrations only]

### **Project Structure**
```
/src
├── /components    # [UI components]
├── /pages         # [Routes/screens] 
├── /lib           # [Core business logic]
├── /utils         # [Shared utilities]
└── /api           # [Backend endpoints]
```

### **Key Architecture Decisions**
- **[Decision 1]:** [Rationale focused on MVP speed]
- **[Decision 2]:** [Rationale focused on simplicity]
- **[Decision 3]:** [Rationale focused on user value]

---

## 🔧 Development Workflow

### **Claude Code MVP Workflow (5-Step)**
1. **`/blueprint`** - @blueprint-specialist: MVP TDD planning + context initialization
2. **Build** - Implement core functionality following TDD
3. **`/qa-review`** - @qa-specialist: Essential quality & security review
4. **`/update-docs`** - @documentation-specialist: Essential documentation updates
5. **`/review-commits`** - @git-specialist: Clean commit organization
6. **`/create-pr`** - @pr-specialist: Production-focused PR documentation

### **Strategic Planning**
Run `/strategic-planning` every 2-3 features to assess:
- User value priorities
- Technical risk mitigation
- Development velocity optimization
- Next MVP iteration focus

### **MVP Development Principles**
- **Ship core functionality fast** - Perfect later
- **Essential quality gates only** - No over-engineering
- **Direct production deployment** - No staging overhead
- **User feedback driven** - Build what users actually need

---

## 📊 Current MVP Status

### **Recently Completed Features**
- **[Feature Name]** *(Shipped: DATE)*
  - **User Value:** [What users can now do]
  - **Key Files:** [Main implementation files]
  - **Production Impact:** [What changed for users]

### **Current Development**
- **Active Feature:** [What's being built now]
- **Status:** [Planning/Building/QA/Ready to Ship]
- **User Impact:** [Why this feature matters]
- **Target Completion:** [When it will be ready]

### **Next MVP Priorities** *(From last `/strategic-planning`)*
1. **[Priority 1]** - User Value: [Direct benefit] - Effort: [S/M/L]
2. **[Priority 2]** - User Value: [Direct benefit] - Effort: [S/M/L]  
3. **[Priority 3]** - User Value: [Direct benefit] - Effort: [S/M/L]

---

## 🧪 MVP Testing Strategy

### **Essential Testing Only**
- **Core User Flows:** [Critical paths users must complete]
- **Security Basics:** [Auth, input validation, data protection]
- **Production Stability:** [No breaking changes to existing features]

### **Test Organization**
- **Unit Tests:** `src/__tests__/` - Core business logic only
- **Integration Tests:** `src/__tests__/integration/` - Critical user flows
- **Manual Testing:** [Key scenarios to verify before shipping]

### **MVP Testing Philosophy**
- **Test core functionality thoroughly**
- **Defer edge case testing until post-MVP**
- **Focus on user-breaking bugs, not perfection**

---

## 🚀 Production Deployment

### **Environment Setup**
```bash
# Essential Environment Variables
DATABASE_URL=[connection string]
API_KEY_AUTH=[authentication service]
APP_URL=[production domain]

# Development Only
NODE_ENV=development
DEBUG_MODE=true
```

### **Deployment Process**
1. **Code Review:** PR review focusing on production readiness
2. **Deploy:** [Platform-specific deployment command]
3. **Verify:** [Quick smoke test of core functionality]
4. **Monitor:** [Key metrics to watch post-deployment]

### **Rollback Procedure**
```bash
# Quick rollback if issues arise
[Platform-specific rollback command]
# Verify rollback worked
[Health check command]
```

---

## 🔐 Essential Security

### **Security Minimums**
- **Authentication:** [Method - JWT, OAuth, etc.]
- **Data Protection:** [User data encryption/handling]
- **Input Validation:** [API endpoint protection]
- **Environment Security:** [Secrets management]

### **Security Checklist**
- [ ] User passwords properly hashed
- [ ] API endpoints validate input
- [ ] Sensitive data not logged
- [ ] Environment variables secured

---

## 📚 Core Business Logic

### **Domain Concepts**
- **[Concept 1]:** [Definition and where implemented]
- **[Concept 2]:** [Definition and where implemented]

### **Critical Business Rules**
- **[Rule 1]:** [What it does and why it matters]
- **[Rule 2]:** [What it does and why it matters]

### **User Flow**
```
User Action → [Processing] → Database/API → User Result
```

---

## 🐛 Known Issues & Technical Debt

### **Ship-Blocking Issues** 
- **[Critical Issue 1]:** [Impact and timeline to fix]
- **[Critical Issue 2]:** [Impact and timeline to fix]

### **Post-MVP Technical Debt**
- **[Debt Item 1]:** [What needs improvement, not urgent]
- **[Debt Item 2]:** [What needs improvement, not urgent]

### **Performance Notes**
- **Current Bottlenecks:** [Known slow areas, acceptable for MVP]
- **Scaling Considerations:** [What to watch as users grow]

---

## 🔄 External Integrations

### **Critical Services**
- **[Service 1]:** [Purpose, auth method, fallback plan]
- **[Service 2]:** [Purpose, auth method, fallback plan]

### **Database Schema** *(Core Tables Only)*
- **Users:** [Key fields and relationships]
- **[Core Entity]:** [Key fields and relationships]

---

## 📈 MVP Metrics & Monitoring

### **Key Success Metrics**
- **User Engagement:** [How you measure success]
- **Core Functionality:** [Usage of main features]
- **Technical Health:** [Error rates, uptime]

### **Essential Monitoring**
- **Error Tracking:** [Platform - Sentry, LogRocket, etc.]
- **Analytics:** [User behavior tracking]
- **Performance:** [Response times, database queries]

### **Alert Thresholds**
- **Critical:** Error rate > [X%], downtime > [X minutes]
- **Warning:** Performance degradation, high resource usage

---

## 👥 Development Conventions

### **Code Style**
- **Formatting:** [Prettier/ESLint config]
- **Naming:** [File and variable conventions]
- **Comments:** [When to comment for MVP speed]

### **Git Workflow**
- **Branches:** `feat/feature-name`, `fix/bug-name`
- **Commits:** Conventional format (feat, fix, docs)
- **PRs:** Focus on production readiness, not perfection

### **MVP Development Standards**
- **Speed over perfection** - Ship working features
- **Essential quality gates** - Security and core functionality
- **Iterate based on feedback** - Build what users actually need

---

## 🚨 Emergency Procedures

### **Production Issues**
1. **Assess Impact:** [User-facing vs internal issue]
2. **Quick Fix:** [Hotfix process]
3. **Rollback:** [Use rollback procedure above]
4. **Communication:** [Who to notify, how]

### **Data Issues**
- **Backup Recovery:** [How to restore data]
- **Data Corruption:** [Detection and mitigation]

---

## 📋 Quick Reference

### **Essential Commands**
```bash
# Development
npm run dev          # Local development
npm run test         # Run essential tests
npm run build        # Production build
npm run deploy       # Deploy to production

# Claude Code MVP Workflow
/blueprint           # Start feature planning
/qa-review          # Essential quality check
/update-docs        # Update this file
/strategic-planning # MVP priority assessment
```

### **Important Links**
- **Production:** [Live app URL]
- **Analytics:** [Dashboard URL]
- **Error Tracking:** [Monitoring dashboard]
- **Repository:** [GitHub/GitLab URL]

---

## 📝 MVP Development History

### **MVP Milestones**
- **[Date]:** [Major milestone - launch, first users, etc.]
- **[Date]:** [Major milestone and impact]

### **Recent Feature History**
*This section is automatically updated by `/update-docs` command*

#### **[Feature Name]** *(Shipped: DATE)*
- **User Value:** [What users can now do]
- **Implementation:** [Key technical approach]
- **Files Changed:** [Primary files modified]
- **Production Impact:** [What changed for users]
- **User Feedback:** [Any early feedback received]
- **Next Iteration:** [How to improve based on usage]

#### **[Feature Name]** *(Shipped: DATE)*
- **User Value:** [What users can now do]
- **Implementation:** [Key technical approach]
- **Files Changed:** [Primary files modified]
- **Production Impact:** [What changed for users]
- **User Feedback:** [Any early feedback received]
- **Next Iteration:** [How to improve based on usage]

---

## 🎯 MVP Strategy Notes

### **Current Phase:** [Core Features/User Validation/Growth/Optimization]

### **Success Metrics This Phase:**
- **Primary Goal:** [Main objective for current phase]
- **Success Criteria:** [How you'll know you've succeeded]
- **Timeline:** [Target completion for current phase]

### **User Feedback Integration**
- **Feedback Collection:** [How you gather user input]
- **Feature Prioritization:** [How feedback influences development]
- **Iteration Cycle:** [How often you release based on feedback]

### **Next Phase Planning**
- **Phase Goal:** [What comes after current phase]
- **Key Features:** [Major features needed for next phase]
- **Technical Requirements:** [Infrastructure needs for scaling]

---

*This document serves as the central context for MVP development. Update after each feature with `/update-docs` to maintain current project state for future development sessions and team coordination.*