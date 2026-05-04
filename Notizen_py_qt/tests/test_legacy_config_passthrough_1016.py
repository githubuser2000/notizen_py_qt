from __future__ import annotations

from xml.etree import ElementTree as ET

from notizen_py_qt.settings import AppSettings


def test_known_legacy_config_elements_keep_unknown_attributes(tmp_path) -> None:
    settings = AppSettings(config_dir=tmp_path)
    xml = '''<?xml version="1.0"?>
<notizen-alx legacy-root="1">
  <scrolls choice="3" vendor="keep-scroll" />
  <language choice="english" marker="keep-language" />
  <open file="notes.alx" directory="/tmp" unknown-open="keep-open">
    <once-opened file="once.alx" timestamp="42" extra-once="keep-once" />
  </open>
  <files a="a.alx" b="" c="" d="" recent-extra="keep-files" />
  <ftp name="u" pass="p" host="h" path="/p" tls="legacy" />
  <main-form x="1" y="2" width="3" height="4" windowstate="Normal" saved-by="old" />
  <tool-stripes old-tool-root="keep-tools">
    <haupt x="5" y="6" dock="top" />
    <font x="7" y="8" dock="bottom" />
  </tool-stripes>
  <desknotes show_desknote_borders="yes" old-desk="keep-desk" />
  <custom-element foo="bar" />
</notizen-alx>
'''
    path = tmp_path / "notizen.config.xml"
    path.write_text(xml, encoding="utf-8")
    settings.apply_from_file(path)
    settings.save()

    root = ET.parse(path).getroot()
    assert root.get("legacy-root") == "1"
    assert root.find("scrolls").get("vendor") == "keep-scroll"  # type: ignore[union-attr]
    assert root.find("language").get("marker") == "keep-language"  # type: ignore[union-attr]
    assert root.find("open").get("unknown-open") == "keep-open"  # type: ignore[union-attr]
    assert root.find("open/once-opened").get("extra-once") == "keep-once"  # type: ignore[union-attr]
    assert root.find("files").get("recent-extra") == "keep-files"  # type: ignore[union-attr]
    assert root.find("ftp").get("tls") == "legacy"  # type: ignore[union-attr]
    assert root.find("main-form").get("saved-by") == "old"  # type: ignore[union-attr]
    assert root.find("tool-stripes").get("old-tool-root") == "keep-tools"  # type: ignore[union-attr]
    assert root.find("tool-stripes/haupt").get("dock") == "top"  # type: ignore[union-attr]
    assert root.find("tool-stripes/font").get("dock") == "bottom"  # type: ignore[union-attr]
    assert root.find("desknotes").get("old-desk") == "keep-desk"  # type: ignore[union-attr]
    assert root.find("custom-element").get("foo") == "bar"  # type: ignore[union-attr]
