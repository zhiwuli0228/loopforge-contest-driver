# Cross-platform Design

LoopForge supports Windows local development and Linux contest execution through a single Python runner plus platform-specific scripts.

## Policy

- Linux is the official submission environment.
- Windows is a supported local development environment.
- `SOURCE_ROOT` may resolve to a contest source mount or to local fallback `.code/`.
- Evaluator-facing outputs stay under `work/result/` and `work/logs/`.
- Internal runtime evidence stays under `work/logs/trace/`.
