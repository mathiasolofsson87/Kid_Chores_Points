# Release
When I say "release", work in two separate steps, each in its own Bash call (never chain them), so a blocked push doesn't undo the local work:
1. Local: run pytest, bump the version in custom_components/kid_chores_points/manifest.json (patch for fixes, minor for features), update CHANGELOG.md, commit.
2. Publish: `git push`, then create the git tag vX.Y.Z and push it, then `gh release create` with notes so HACS picks it up. Run these as separate calls too.
Ask before step 2 if I said "don't push yet".

# Roadmap
Improvement ideas live in ROADMAP.md at the repo root.
