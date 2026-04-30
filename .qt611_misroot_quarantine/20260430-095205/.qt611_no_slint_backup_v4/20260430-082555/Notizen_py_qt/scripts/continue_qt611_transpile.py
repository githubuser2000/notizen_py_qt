#!/usr/bin/env python3
"""One-shot continuation for the Qt 6.11 / no-Slint migration.

It runs the previous fixers in the right order and keeps going after non-fatal
scanner failures so the next fixer still gets a chance to clean the project.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Step:
    name: str
    command: list[str]
    fatal: bool = False


@dataclass
class Result:
    name: str
    returncode: int
    output: str


def run_step(step: Step, cwd: Path) -> Result:
    proc = subprocess.run(step.command, cwd=str(cwd), text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return Result(step.name, proc.returncode, proc.stdout)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Continue the Qt 6.11 migration")
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--restore-controller", action="store_true", default=True, help="recover and port the old app.py controller from backups")
    parser.add_argument("--no-restore-controller", dest="restore_controller", action="store_false")
    parser.add_argument("--probe", action="store_true", help="also run the runtime probe after source rewriting")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    script_dir = Path(__file__).resolve().parent
    apply_flag = ["--apply"] if args.apply else []
    py = sys.executable

    steps: list[Step] = [
        Step("repair pyproject", [py, str(script_dir / "repair_pyproject_qt611.py"), str(root), *apply_flag]),
        Step("finish Python package migration", [py, str(script_dir / "finish_python_qt_migration.py"), str(root), *apply_flag]),
        Step("repair pyproject again", [py, str(script_dir / "repair_pyproject_qt611.py"), str(root), *apply_flag]),
        Step("harden QML", [py, str(script_dir / "fix_qml_for_pyside.py"), str(root), *apply_flag]),
        Step("harden Python/Qt runtime", [py, str(script_dir / "harden_python_qt_runtime.py"), str(root), *apply_flag]),
    ]
    if args.restore_controller:
        steps.append(Step("restore Qt controller from backup", [py, str(script_dir / "restore_qt_controller_from_backup.py"), str(root), *apply_flag]))
    steps.extend([
        Step("final pyproject repair", [py, str(script_dir / "repair_pyproject_qt611.py"), str(root), *apply_flag]),
        Step("QML sanity check", [py, str(script_dir / "qml_sanity_check.py"), str(root)]),
        Step("analyze migration", [py, str(script_dir / "analyze_transpilation.py"), str(root), "--write"]),
        Step("old framework scanner", ["bash", str(script_dir / "check_no_slint.sh"), str(root)]),
    ])
    if args.probe:
        steps.append(Step("Python/Qt runtime probe", [py, str(script_dir / "probe_python_qt_runtime.py"), str(root)]))

    results: list[Result] = []
    final_rc = 0
    print(f"Mode: {'APPLY' if args.apply else 'DRY-RUN'}")
    print(f"Root: {root}")
    print("\nSteps:")
    for step in steps:
        print(f"\n=== {step.name} ===")
        result = run_step(step, cwd=script_dir)
        results.append(result)
        print(result.output.rstrip())
        if result.returncode != 0:
            print(f"[step returned {result.returncode}]")
            if step.fatal:
                final_rc = result.returncode
                break
            # Source-rewriting steps and the analyzer can legitimately return
            # non-zero before later cleanup passes finish. Only the final hard
            # checks should make this wrapper fail.
            if step.name in {"QML sanity check", "old framework scanner", "Python/Qt runtime probe"}:
                final_rc = result.returncode

    report = root / "QT611_CONTINUE_TRANSPILE_REPORT.md"
    lines = [
        "# Qt 6.11 continued transpilation report",
        "",
        f"Mode: {'APPLY' if args.apply else 'DRY-RUN'}",
        f"Root: `{root}`",
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
        lines.append(result.output.rstrip()[-12000:])
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
        print("\nFinished with remaining issues. Open QT611_CONTINUE_TRANSPILE_REPORT.md for the exact next target.")
    return final_rc


if __name__ == "__main__":
    raise SystemExit(main())
