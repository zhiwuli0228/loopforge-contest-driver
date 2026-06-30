# Cross-platform Design

LoopForge supports Windows local development and Linux contest execution through a single Python runner plus platform-specific scripts.

## Policy

- Linux is the official submission environment.
- Windows is a supported local development environment.
- On non-Windows systems, `SOURCE_ROOT` resolves from the explicit value or contest platform mount; Windows defaults to `work/code/`.
- Evaluator-facing outputs stay under `work/result/` and `work/logs/`.
- Internal runtime evidence stays under `work/logs/trace/`.
