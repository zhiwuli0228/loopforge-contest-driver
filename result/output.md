# Output

- source_root: `E:\009workspace\codex\loopforge-contest-driver\code-gulimall-backup`
- resolved_code_dir: `E:\009workspace\codex\loopforge-contest-driver\code-gulimall-backup`
- artifact_dir: `E:\009workspace\codex\loopforge-contest-driver\code-gulimall-backup\.loopforge`
- result: `BLOCKED_WITH_REPORT`
- verification_status: `blocked-with-report`
- final_report: `E:\009workspace\codex\loopforge-contest-driver\code-gulimall-backup\.loopforge\reports\final-report.md`

## Self Check

{
  "ok": false,
  "checks": {
    "python_version": "3.14.4",
    "workspace_root": "E:\\009workspace\\codex\\loopforge-contest-driver",
    "work_dir_exists": true,
    "code_dir_exists": true,
    "config_exists": true,
    "artifact_dir_target": "E:\\009workspace\\codex\\loopforge-contest-driver\\code-gulimall-backup\\.loopforge",
    "artifact_dir_under_code": true,
    "verification_commands_configured": true,
    "verification_working_directory": "code",
    "runner_copied": true,
    "config_contract_ok": false,
    "profile_contract_ok": true,
    "work_package_contract_ok": true,
    "coding_skill_status": "CODING_SKILL_MISSING",
    "coding_skill_contract_ok": false
  },
  "contract_summary": {
    "ok": false,
    "errors": [
      "coding_skill.enabled must be true",
      "coding_skill.required must be true",
      "coding_skill.skill must be skills/code-implementation/SKILL.md",
      "coding_skill.apply_at must include patch_implementation",
      "coding_skill.output must be code/.loopforge/consistency/05-patch-summary.md",
      "coding_skill.output is required",
      "CODING_SKILL_MISSING: coding skill file not found"
    ],
    "warnings": [],
    "platform": {
      "configured_work_dir": "E:\\009workspace\\codex\\loopforge-contest-driver\\work",
      "configured_code_dir": "E:\\009workspace\\codex\\loopforge-contest-driver\\code-gulimall-backup",
      "artifact_dir": "E:\\009workspace\\codex\\loopforge-contest-driver\\code-gulimall-backup\\.loopforge"
    },
    "task": {
      "mode": "feature-development",
      "profile": "profiles/templates/feature-development.yaml"
    },
    "verification": {
      "working_directory": "E:\\009workspace\\codex\\loopforge-contest-driver\\code-gulimall-backup",
      "commands_format": "platform-map",
      "available_profiles": [
        "default",
        "linux",
        "windows"
      ],
      "selected_profile": "windows",
      "fallback_used": false,
      "commands_count": 1
    },
    "governance": {
      "ok": true,
      "superspec": "",
      "superpower": "",
      "mode_rules": [],
      "delegated_staged_ready": false
    },
    "subagent_contract": {
      "ok": true,
      "errors": [],
      "warnings": [],
      "stage_count": 0,
      "stages": []
    },
    "coding_skill": {
      "ok": false,
      "errors": [
        "coding_skill.enabled must be true",
        "coding_skill.required must be true",
        "coding_skill.skill must be skills/code-implementation/SKILL.md",
        "coding_skill.apply_at must include patch_implementation",
        "coding_skill.output must be code/.loopforge/consistency/05-patch-summary.md",
        "coding_skill.output is required",
        "CODING_SKILL_MISSING: coding skill file not found"
      ],
      "warnings": [],
      "enabled": false,
      "required": false,
      "skill": "",
      "apply_at": [],
      "output": "",
      "ready_status": "CODING_SKILL_MISSING",
      "skill_exists": false,
      "references_ready": false,
      "stage_declared": false,
      "superpower_policy_ready": false
    },
    "outputs": {
      "consistency_dir": "E:\\009workspace\\codex\\loopforge-contest-driver\\code-gulimall-backup\\.loopforge\\consistency",
      "final_report": "E:\\009workspace\\codex\\loopforge-contest-driver\\code-gulimall-backup\\.loopforge\\reports\\final-report.md",
      "patch_snapshot_dir": "E:\\009workspace\\codex\\loopforge-contest-driver\\code-gulimall-backup\\.loopforge\\snapshots"
    },
    "profile_summary": {
      "ok": true,
      "errors": [],
      "warnings": [],
      "profile_path": "E:\\009workspace\\codex\\loopforge-contest-driver\\work\\profiles\\templates\\feature-development.yaml",
      "profile_name": "feature-development-template",
      "profile_class": "template",
      "task_mode": "feature-development"
    },
    "work_package_summary": {
      "ok": true,
      "errors": [],
      "warnings": [],
      "required_files_present": [
        "INSTRUCTION.md",
        "README.md",
        "SUBMISSION.md",
        "loopforge.config.yaml",
        "HARNESS.md",
        "runtime/loopforge_runner.py",
        "scripts/bootstrap.sh",
        "scripts/bootstrap.ps1",
        "scripts/smoke-test.sh",
        "scripts/smoke-test.ps1",
        "skills/loopforge-driver/SKILL.md",
        "docs/DESIGN.md",
        "docs/ADAPTATION_GUIDE.md",
        "docs/CROSS_PLATFORM_DESIGN.md",
        "docs/DAILY_DEV_USAGE.md",
        "profiles/README.md",
        "rules/loopforge/core/00-core.md",
        "rules/loopforge/core/01-work-code-boundary.md",
        "rules/loopforge/core/02-static-rule-ownership.md",
        "rules/loopforge/core/03-verification-contract.md",
        "rules/loopforge/core/04-gate-policy.md",
        "rules/loopforge/core/05-final-report.md",
        "rules/loopforge/core/06-code-generation-boundary.md"
      ],
      "required_files_missing": [],
      "available_modes": {
        "consistency-check": [
          "00-flow.md",
          "01-phase-policy.md",
          "02-required-artifacts.md",
          "03-forbidden-actions.md",
          "04-final-report.md"
        ],
        "defect-repair": [
          "00-flow.md",
          "01-phase-policy.md",
          "02-required-artifacts.md",
          "03-forbidden-actions.md",
          "04-final-report.md"
        ],
        "feature-development": [
          "00-flow.md",
          "01-phase-policy.md",
          "02-required-artifacts.md",
          "03-forbidden-actions.md",
          "04-final-report.md"
        ],
        "migration": [
          "00-flow.md",
          "01-phase-policy.md",
          "02-required-artifacts.md",
          "03-forbidden-actions.md",
          "04-final-report.md"
        ],
        "skill-generation": [
          "00-flow.md",
          "01-phase-policy.md",
          "02-required-artifacts.md",
          "03-forbidden-actions.md",
          "04-final-report.md"
        ]
      },
      "configured_mode": "feature-development",
      "template_count": 5,
      "example_count": 5
    }
  }
}

## Detection

{
  "project_type": "java-maven",
  "indicators": {
    "pom.xml": true,
    "mvnw": false,
    "pyproject.toml": false,
    "requirements.txt": false,
    "package.json": false,
    "go.mod": false,
    "git_worktree": true
  }
}

## Verification

{
  "ok": false,
  "status": "blocked-with-report",
  "reason": "runtime contract validation failed before verification",
  "contract_summary": {
    "ok": false,
    "errors": [
      "coding_skill.enabled must be true",
      "coding_skill.required must be true",
      "coding_skill.skill must be skills/code-implementation/SKILL.md",
      "coding_skill.apply_at must include patch_implementation",
      "coding_skill.output must be code/.loopforge/consistency/05-patch-summary.md",
      "coding_skill.output is required",
      "CODING_SKILL_MISSING: coding skill file not found"
    ],
    "warnings": [],
    "platform": {
      "configured_work_dir": "E:\\009workspace\\codex\\loopforge-contest-driver\\work",
      "configured_code_dir": "E:\\009workspace\\codex\\loopforge-contest-driver\\code-gulimall-backup",
      "artifact_dir": "E:\\009workspace\\codex\\loopforge-contest-driver\\code-gulimall-backup\\.loopforge"
    },
    "task": {
      "mode": "feature-development",
      "profile": "profiles/templates/feature-development.yaml"
    },
    "verification": {
      "working_directory": "E:\\009workspace\\codex\\loopforge-contest-driver\\code-gulimall-backup",
      "commands_format": "platform-map",
      "available_profiles": [
        "default",
        "linux",
        "windows"
      ],
      "selected_profile": "windows",
      "fallback_used": false,
      "commands_count": 1
    },
    "governance": {
      "ok": true,
      "superspec": "",
      "superpower": "",
      "mode_rules": [],
      "delegated_staged_ready": false
    },
    "subagent_contract": {
      "ok": true,
      "errors": [],
      "warnings": [],
      "stage_count": 0,
      "stages": []
    },
    "coding_skill": {
      "ok": false,
      "errors": [
        "coding_skill.enabled must be true",
        "coding_skill.required must be true",
        "coding_skill.skill must be skills/code-implementation/SKILL.md",
        "coding_skill.apply_at must include patch_implementation",
        "coding_skill.output must be code/.loopforge/consistency/05-patch-summary.md",
        "coding_skill.output is required",
        "CODING_SKILL_MISSING: coding skill file not found"
      ],
      "warnings": [],
      "enabled": false,
      "required": false,
      "skill": "",
      "apply_at": [],
      "output": "",
      "ready_status": "CODING_SKILL_MISSING",
      "skill_exists": false,
      "references_ready": false,
      "stage_declared": false,
      "superpower_policy_ready": false
    },
    "outputs": {
      "consistency_dir": "E:\\009workspace\\codex\\loopforge-contest-driver\\code-gulimall-backup\\.loopforge\\consistency",
      "final_report": "E:\\009workspace\\codex\\loopforge-contest-driver\\code-gulimall-backup\\.loopforge\\reports\\final-report.md",
      "patch_snapshot_dir": "E:\\009workspace\\codex\\loopforge-contest-driver\\code-gulimall-backup\\.loopforge\\snapshots"
    },
    "profile_summary": {
      "ok": true,
      "errors": [],
      "warnings": [],
      "profile_path": "E:\\009workspace\\codex\\loopforge-contest-driver\\work\\profiles\\templates\\feature-development.yaml",
      "profile_name": "feature-development-template",
      "profile_class": "template",
      "task_mode": "feature-development"
    },
    "work_package_summary": {
      "ok": true,
      "errors": [],
      "warnings": [],
      "required_files_present": [
        "INSTRUCTION.md",
        "README.md",
        "SUBMISSION.md",
        "loopforge.config.yaml",
        "HARNESS.md",
        "runtime/loopforge_runner.py",
        "scripts/bootstrap.sh",
        "scripts/bootstrap.ps1",
        "scripts/smoke-test.sh",
        "scripts/smoke-test.ps1",
        "skills/loopforge-driver/SKILL.md",
        "docs/DESIGN.md",
        "docs/ADAPTATION_GUIDE.md",
        "docs/CROSS_PLATFORM_DESIGN.md",
        "docs/DAILY_DEV_USAGE.md",
        "profiles/README.md",
        "rules/loopforge/core/00-core.md",
        "rules/loopforge/core/01-work-code-boundary.md",
        "rules/loopforge/core/02-static-rule-ownership.md",
        "rules/loopforge/core/03-verification-contract.md",
        "rules/loopforge/core/04-gate-policy.md",
        "rules/loopforge/core/05-final-report.md",
        "rules/loopforge/core/06-code-generation-boundary.md"
      ],
      "required_files_missing": [],
      "available_modes": {
        "consistency-check": [
          "00-flow.md",
          "01-phase-policy.md",
          "02-required-artifacts.md",
          "03-forbidden-actions.md",
          "04-final-report.md"
        ],
        "defect-repair": [
          "00-flow.md",
          "01-phase-policy.md",
          "02-required-artifacts.md",
          "03-forbidden-actions.md",
          "04-final-report.md"
        ],
        "feature-development": [
          "00-flow.md",
          "01-phase-policy.md",
          "02-required-artifacts.md",
          "03-forbidden-actions.md",
          "04-final-report.md"
        ],
        "migration": [
          "00-flow.md",
          "01-phase-policy.md",
          "02-required-artifacts.md",
          "03-forbidden-actions.md",
          "04-final-report.md"
        ],
        "skill-generation": [
          "00-flow.md",
          "01-phase-policy.md",
          "02-required-artifacts.md",
          "03-forbidden-actions.md",
          "04-final-report.md"
        ]
      },
      "configured_mode": "feature-development",
      "template_count": 5,
      "example_count": 5
    }
  }
}
