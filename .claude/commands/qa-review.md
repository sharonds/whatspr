# /qa-review

**FEATURE CONTEXT:** [SPECIFY_FEATURE_NAME]
**CHANGED FILES:** [OUTPUT OF: git diff --staged --name-only]

@qa-specialist Please review ONLY these specific files for MVP feature: **[FEATURE_NAME]**

**Context Loading:**
1. Read `CLAUDE.md` sections: Security Considerations, Known Issues (ONLY)
2. Focus on changed files listed above (no broad scanning)
3. MVP production readiness assessment

**Changed Files to Review:**
```bash
# Provide exact file list
[FILE_1] - [Purpose]
[FILE_2] - [Purpose]
[FILE_3] - [Purpose]
```

**MVP Review Scope:**
- 🚨 **Critical Issues** - Security vulnerabilities, breaking changes
- ⚠️ **Production Safety** - Won't break existing functionality
- ✅ **Core Functionality** - Feature works as intended
- 🔧 **Essential Tests** - Core scenarios covered

**MVP Focus:** Ship-blocking issues only. Defer perfection to post-MVP iterations.

**Fallback:** If @qa-specialist unavailable, review for critical security issues and production safety only.
