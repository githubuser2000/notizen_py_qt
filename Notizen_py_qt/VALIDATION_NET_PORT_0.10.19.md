# Validierung 0.10.19

## Ausgeführte Prüfungen

```bash
python3 -m compileall -q src notizen_py_qt scripts
bash -n notizen-starten.sh "Notizen starten.sh" notizen-starten-venv.sh scripts/install_linux_launcher.sh scripts/uninstall_linux_launcher.sh scripts/build_linux_appdir.sh
pytest -q
# zusätzlich in temporärem XDG_DATA_HOME:
./scripts/install_linux_launcher.sh
```

## Ergebnis

- Python-Quellen und Skripte kompilieren beziehungsweise bestehen die Bash-Syntaxprüfung.
- Testlauf: `196 passed, 2 skipped`.
- Testinstallation in temporärem `XDG_DATA_HOME` schreibt `notizen-py-qt.desktop` mit absolutem Launcherpfad und entfernt die stale `Notizen PyQt.desktop`-Kopie.

## Hinweis zur Umgebung

In dieser Containerumgebung ist keine echte GNOME-Shell/Qt-Display-Sitzung vorhanden. Der GNOME-Menüstart wurde deshalb strukturell über `.desktop`-Inhalte, Installationsskript, Cache-/Stale-Datei-Behandlung und Startargumente geprüft. Die reale Menüintegration sollte nach dem Entpacken mit folgendem Befehl neu installiert werden:

```bash
./scripts/install_linux_launcher.sh
```

Falls ein alter Eintrag weiter im GNOME-Menü hängt, einmal ab- und wieder anmelden oder GNOME Shell neu laden; der Installer entfernt die bekannte stale Menüdatei bereits automatisch.
