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
