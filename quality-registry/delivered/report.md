- **Every claim carries its rung and reaches its floor** (`_quality/CONTRACT.md`
  §1-2): `E0` reasoning alone never ships · `E1` static · `E2` execution · `E3`
  automated test · `E4` independent oracle · `E5` integration · `E6` production.
  A claim that cannot reach its floor is **not downgraded and shipped anyway** —
  it is emitted as a `HYPOTHESIS` with the one command that would settle it
- **Report `status`**: `DONE` (every claim at floor, every residual classified) /
  `PARTIAL` / `BLOCKED` (say what was tried)
- **Every residual is `BLOCKED` / `OUT-OF-SCOPE` / `DEFERRED` / `HYPOTHESIS`**
  and appears in the handoff's `open`; a run holding `Write` also leaves a
  `#TODO(agent):` marker carrying that class where a reader would next look
- **Never omit the sweep** — markers against `open`, claims made against claims
  at floor: `swept, 0 markers; 9 claims / 9 at floor`. While either pair
  disagrees the status is not `DONE`
