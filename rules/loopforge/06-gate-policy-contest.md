# Contest Gate Policy

## Gate States

- `PASS`
- `WARN`
- `RETRY`
- `REPAIR`
- `DEGRADE`
- `BLOCK`

## Policy

- Prefer continuing execution over early termination.
- Route ordinary failures into retry, repair, or degrade.
- Reserve `BLOCK` for destructive, unsafe, or unrecoverable conditions.
- Finalization must still be attempted whenever possible.

## Block Conditions

- target repository cannot be read
- required writes are impossible
- work tree is unrecoverably corrupted
- a dangerous or destructive action is required
- the runner and degraded mode both fail to produce any report
