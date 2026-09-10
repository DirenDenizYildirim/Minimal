#!/usr/bin/env bash
# Archive `results/` to the `results-archive` branch, one tarball per phase.
#
#   scripts/archive_results.sh phase-2-searched-s3
#
# WHY THIS EXISTS. `results/` is gitignored and regenerable in principle, but
# Phase 0 measured what "in principle" costs: 11 hours of wall time, and three
# groups of §13 rows that turned out NOT to regenerate at all because the
# provenance to reproduce them was never recorded. An archive is the difference
# between "we can rebuild this" and "we can check what we actually had".
#
# The archive branch is an ORPHAN: it shares no history with the work branch, so
# a 13 MB tarball per phase never lands in a `git log` or a diff of the code.
# Each commit carries a manifest — file count, byte size, and the sha256 of every
# results file — so a later reader can tell whether an unpacked copy is the one
# that produced a number without unpacking the tarball at all.
set -euo pipefail
cd "$(dirname "$0")/.."

LABEL="${1:?usage: archive_results.sh <phase-label>}"
BRANCH=results-archive
HASH=$(git rev-parse --short HEAD)
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
NAME="results-${STAMP}-${HASH}-${LABEL}"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
  echo "refusing to archive with uncommitted tracked changes: the archive would" >&2
  echo "record a commit hash that does not describe the tree that produced it." >&2
  exit 1
fi

echo "packing results/ ($(du -sh results | cut -f1)) as ${NAME}.tgz"
tar -czf "$WORK/${NAME}.tgz" results/
{
  echo "# ${NAME}"
  echo
  echo "Produced at \`${HASH}\` on \`$(git rev-parse --abbrev-ref HEAD)\`, $(date -u +%Y-%m-%dT%H:%MZ)."
  echo "Phase: ${LABEL}."
  echo
  echo "\`\`\`"
  echo "files      $(find results -type f ! -name .gitkeep | wc -l)"
  echo "bytes      $(du -sb results | cut -f1)"
  echo "tarball    $(du -sb "$WORK/${NAME}.tgz" | cut -f1)"
  echo "\`\`\`"
  echo
  echo "## sha256 of every results file"
  echo
  echo "\`\`\`"
  (cd results && find . -type f ! -name .gitkeep -print0 | sort -z | xargs -0 sha256sum)
  echo "\`\`\`"
} > "$WORK/${NAME}.md"

# A detached worktree, so the working tree and its 195 MB of results are never
# touched and a failure here cannot leave the work branch checked out elsewhere.
if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
  git worktree add -f "$WORK/wt" "$BRANCH" >/dev/null
else
  git worktree add -f --detach "$WORK/wt" >/dev/null
  git -C "$WORK/wt" checkout --orphan "$BRANCH" >/dev/null
  git -C "$WORK/wt" rm -rq --cached . 2>/dev/null || true
  find "$WORK/wt" -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +
  cat > "$WORK/wt/README.md" <<'EOF'
# results-archive

Tarballs of `results/` for *Minimal swarms in hostile environments*, one per
phase of the freeze lift, with a manifest beside each.

This branch is an **orphan**: it shares no history with the work branch, so the
tarballs never appear in a code diff. Nothing here is an input to anything —
every file in a tarball is regenerable from `configs/` and `docs/run-log.md`.
What the archive adds is the ability to *check* a number against the bytes that
produced it, rather than against a re-run that may differ for a reason nobody
has noticed yet. Phase 0 found three such reasons.

Each `.md` manifest carries the sha256 of every file in its tarball, so an
unpacked copy can be identified without unpacking the archive.
EOF
fi

cp "$WORK/${NAME}.tgz" "$WORK/${NAME}.md" "$WORK/wt/"
git -C "$WORK/wt" add -A
git -C "$WORK/wt" -c user.email=noreply@anthropic.com -c user.name=Claude \
  commit -q -m "Archive results/ at ${HASH} — ${LABEL}"
git -C "$WORK/wt" push -q -u origin "$BRANCH"
echo "pushed $(git -C "$WORK/wt" rev-parse --short HEAD) to $BRANCH: ${NAME}.tgz"
git worktree remove --force "$WORK/wt"
