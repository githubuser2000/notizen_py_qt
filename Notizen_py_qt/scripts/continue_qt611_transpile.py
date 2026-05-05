#!/usr/bin/env python3
"""Continue the Qt 6.11 migration safely after a parent-folder mis-run."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from qt611_project_utils import describe_root_choice, find_project_root  # noqa: E402


@dataclass
class Step:
    name: str
    command: list[str]
    fatal: bool = False
    timeout: int | None = None


@dataclass
class Result:
    name: str
    returncode: int
    output: str


def _default_step_timeout() -> int:
    try:
        return max(10, int(os.environ.get("QT611_CONTINUE_STEP_TIMEOUT", "120")))
    except ValueError:
        return 120


def run_step(step: Step, cwd: Path) -> Result:
    timeout = step.timeout if step.timeout is not None else _default_step_timeout()
    try:
        proc = subprocess.run(
            step.command,
            cwd=str(cwd),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
        )
        return Result(step.name, proc.returncode, proc.stdout)
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        return Result(step.name, 124, stdout + f"\n[TIMEOUT after {timeout}s]\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Continue the Qt 6.11 migration with project-root auto-detection")
    parser.add_argument("root", nargs="?", default=".", help="Project root, parent folder, or pyproject.toml")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--restore-controller", action="store_true", default=True)
    parser.add_argument("--no-restore-controller", dest="restore_controller", action="store_false")
    parser.add_argument("--probe", action="store_true", help="also run the runtime probe after source rewriting")
    parser.add_argument("--no-clean-misroot", action="store_true", help="do not quarantine accidental parent-folder artifacts")
    args = parser.parse_args(argv)

    input_root = Path(args.root).resolve()
    project_root = find_project_root(input_root)
    apply_flag = ["--apply"] if args.apply else []
    py = sys.executable

    steps: list[Step] = []
    if project_root != input_root and not args.no_clean_misroot:
        steps.append(Step(
            "recover parent-folder mis-run",
            [py, str(SCRIPT_DIR / "recover_misrooted_qt611_migration.py"), str(input_root), "--project-root", str(project_root), *apply_flag],
        ))

    steps.extend([
        Step("repair pyproject", [py, str(SCRIPT_DIR / "repair_pyproject_qt611.py"), str(project_root), *apply_flag], fatal=False),
        Step("finish Python package migration", [py, str(SCRIPT_DIR / "finish_python_qt_migration.py"), str(project_root), *apply_flag], fatal=False),
        Step("repair pyproject again", [py, str(SCRIPT_DIR / "repair_pyproject_qt611.py"), str(project_root), *apply_flag], fatal=False),
        Step("harden QML", [py, str(SCRIPT_DIR / "fix_qml_for_pyside.py"), str(project_root), *apply_flag], fatal=False),
        Step("comment generated TODO code blocks", [py, str(SCRIPT_DIR / "repair_qml_todo_blocks.py"), str(project_root), *apply_flag], fatal=False),
        Step("harden Python/Qt runtime", [py, str(SCRIPT_DIR / "harden_python_qt_runtime.py"), str(project_root), *apply_flag], fatal=False),
    ])
    if args.restore_controller:
        steps.append(Step("restore Qt controller from backup", [py, str(SCRIPT_DIR / "restore_qt_controller_from_backup.py"), str(project_root), *apply_flag], fatal=False))
    steps.extend([
        Step("final pyproject repair", [py, str(SCRIPT_DIR / "repair_pyproject_qt611.py"), str(project_root), *apply_flag], fatal=False),
        Step("QML sanity check", [py, str(SCRIPT_DIR / "qml_sanity_check.py"), str(project_root)], fatal=False),
        Step("analyze migration", [py, str(SCRIPT_DIR / "analyze_transpilation.py"), str(project_root), "--write"], fatal=False),
        Step("old framework scanner", ["bash", str(SCRIPT_DIR / "check_no_slint.sh"), str(project_root)], fatal=False),
    ])
    if args.probe:
        steps.append(Step("repair QML engine errors", [py, str(SCRIPT_DIR / "repair_qml_engine_errors.py"), str(project_root), *apply_flag, "--run-smoke", "--static-padding-pass", "--max-rounds", "12", "--python", py], fatal=False))
        steps.append(Step("Python/Qt runtime probe", [py, str(SCRIPT_DIR / "probe_python_qt_runtime.py"), str(project_root)], fatal=False))

    results: list[Result] = []
    final_rc = 0
    print(f"Mode: {'APPLY' if args.apply else 'DRY-RUN'}")
    print(describe_root_choice(input_root))
    print("\nSteps:")

    for step in steps:
        print(f"\n=== {step.name} ===")
        result = run_step(step, cwd=SCRIPT_DIR)
        results.append(result)
        rendered_output = result.output.rstrip()
        if len(rendered_output) > 12000:
            rendered_output = rendered_output[:4000] + "\n... [output truncated] ...\n" + rendered_output[-4000:]
        print(rendered_output)
        if result.returncode != 0:
            print(f"[step returned {result.returncode}]")
            if step.fatal:
                final_rc = result.returncode
                break
            if step.name in {"QML sanity check", "old framework scanner", "Python/Qt runtime probe"}:
                final_rc = result.returncode

    report = project_root / "QT611_CONTINUE_TRANSPILE_REPORT.md"
    lines = [
        "# Qt 6.11 continued transpilation report",
        "",
        f"Mode: {'APPLY' if args.apply else 'DRY-RUN'}",
        f"Input root: `{input_root}`",
        f"Detected project root: `{project_root}`",
        "",
        "## Step results",
        "",
    ]
    for result in results:
        lines.append(f"### {result.name}")
        lines.append("")
        lines.append(f"Return code: `{result.returncode}`")
        lines.append("")
        lines.append("```text")
        lines.append(result.output.rstrip()[-16000:])
        lines.append("```")
        lines.append("")
    if args.apply:
        report.write_text("\n".join(lines), encoding="utf-8")
        print(f"\nWrote report: {report}")
    else:
        print("\nDry-run only; no report written.")

    if final_rc == 0:
        print("\nOK: continued transpilation finished without scanner errors.")
    else:
        print("\nFinished with remaining issues. Open QT611_CONTINUE_TRANSPILE_REPORT.md in the detected project root.")
    return final_rc


if __name__ == "__main__":
    raise SystemExit(main())
