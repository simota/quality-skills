- **Every claim carries its actual rung and is warranted for that claim** (`_quality/CONTRACT.md`
  §1-3): `E0` reasoning alone never ships · `E1` static · `E2` execution · `E3` automated test ·
  `E4` independent oracle · `E5` integration · `E6` production. A command that ran proves nothing
  about a different claim; `E4` needs a traced independent expectation, not a different agent
- **A claim that cannot reach its floor is not downgraded and shipped anyway** — it is a
  `HYPOTHESIS` with the observation or safe check that would settle it. A bounded `E1` proof may
  establish a defect; missing evidence never does. Narrowing a claim does not close the
  original question's unresolved parts
- **Report `status`**: `DONE` (every claim warranted, every residual classified) / `PARTIAL` / `BLOCKED`
- **Every residual is `BLOCKED` / `OUT-OF-SCOPE` / `DEFERRED` / `HYPOTHESIS`**
  and appears in the handoff's `open`; a run holding `Write` also leaves a
  `#TODO(agent):` marker carrying that class where a reader would next look
- **Never omit the sweep** — markers against `open`, claims made against claims warranted:
  `swept, 0 markers; 9 claims / 9 warranted`. While either pair disagrees the status is not `DONE`
