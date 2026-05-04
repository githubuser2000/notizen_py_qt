from __future__ import annotations

import os
import subprocess
from pathlib import Path


def test_optional_venv_launcher_delegates_to_visible_start_script() -> None:
    script = Path("notizen-starten-venv.sh")
    text = script.read_text(encoding="utf-8")
    assert os.access(script, os.X_OK)
    assert "python3" in text
    assert "-m venv" in text
    assert 'notizen-starten.sh" "$@"' in text
    assert "NOTIZEN_VENV_DIR" in text


def test_optional_venv_launcher_shell_syntax_is_valid() -> None:
    subprocess.run(["bash", "-n", "notizen-starten-venv.sh"], check=True)



def test_linux_launcher_installer_can_select_optional_venv_launcher() -> None:
    text = Path("scripts/install_linux_launcher.sh").read_text(encoding="utf-8")
    assert "--venv" in text
    assert "notizen-starten-venv.sh" in text
    assert "USE_VENV_LAUNCHER" in text
