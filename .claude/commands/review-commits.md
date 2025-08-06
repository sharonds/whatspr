# /review-commits

**FEATURE CONTEXT:** [SPECIFY_FEATURE_NAME]  
**SCOPE:** [BRIEF_IMPLEMENTATION_SUMMARY]

@git-specialist Examine `git diff --staged` and organize changes for MVP feature: **[FEATURE_NAME]**

**MVP Commit Strategy:**
1. **Logical grouping** - Related changes together (tests + implementation OK)
2. **Conventional format** - feat/fix/docs prefixes
3. **Production-ready commits** - Each commit should be deployable
4. **Minimal commit count** - Group related changes, avoid micro-commits

**Required Output:**
```bash
# Exact MVP-optimized commands:
git reset
git add [logically related files]
git commit -m "feat: feature description"
# Fewer, cleaner commits for MVP speed
```

**MVP Approach:** Prioritize clear, deployable commits over atomic perfection.

**Fallback:** If @git-specialist unavailable, organize into logical conventional commits prioritizing deployability over atomicity.

Provide the specific `git add` and `git commit` commands in execution order.
