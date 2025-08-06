# /create-pr

**FEATURE CONTEXT:** [SPECIFY_FEATURE_NAME]
**IMPLEMENTATION:** [BRIEF_CHANGES_SUMMARY]

@pr-specialist Create streamlined PR description for MVP feature: **[FEATURE_NAME]**

**MVP PR Requirements:**
1. **Core functionality** - What this feature does (1-2 sentences)
2. **Production impact** - What changes for users
3. **Testing verification** - How to confirm it works
4. **Deployment readiness** - Production deployment notes
5. **Rollback plan** - How to revert if needed

**MVP PR Format:**
```markdown
## MVP Feature: [Name]
[Brief core functionality description]

## Production Changes
- **User impact:** [What users experience]
- **Technical changes:** [Key implementation notes]

## Verification
- [ ] Core functionality tested
- [ ] No breaking changes
- [ ] Production ready

## Rollback
[Quick revert procedure]
```

**Length:** Max 150 words - focused on production deployment decisions.

**Fallback:** If @pr-specialist unavailable, create concise PR focusing on production readiness and rollback procedures.
