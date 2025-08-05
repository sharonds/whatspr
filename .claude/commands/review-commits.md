# /review-commits

**FEATURE CONTEXT:** [Use /context-sync first if context unclear]

Feature Name: [SPECIFY_FEATURE_NAME]
Scope: [BRIEF_WHAT_WAS_IMPLEMENTED]

@git-specialist Please examine `git diff --staged` and organize changes for feature: **[FEATURE_NAME]**

**Commit Organization Requirements:**
1. **Atomic Commits** - Each commit should be independently functional
2. **Logical Grouping** - Separate tests, implementation, docs, config
3. **Conventional Format** - Use feat/fix/test/docs/refactor/chore prefixes
4. **Clear Messages** - Under 50 characters, imperative mood

**Required Output:**
```bash
# Exact commands to execute:
git reset
git add [specific files]
git commit -m "type: clear description"
# Repeat for each logical group
```

**Fallback:** If @git-specialist unavailable, organize commits using conventional commit format with atomic, logical groupings.

Provide the specific `git add` and `git commit` commands in execution order.
