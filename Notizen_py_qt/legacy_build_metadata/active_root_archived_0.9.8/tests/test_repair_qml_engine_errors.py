from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from repair_qml_engine_errors import parse_engine_errors, patch_file_line, patch_line_for_error  # noqa: E402


def test_parse_engine_error_file_uri() -> None:
    text = 'file:///tmp/proj/src/notizen_py_qt/ui/Main.qml:77:9: Cannot assign to non-existent property "padding"'
    errors = parse_engine_errors(text)
    assert len(errors) == 1
    assert errors[0].path == Path('/tmp/proj/src/notizen_py_qt/ui/Main.qml')
    assert errors[0].line == 77
    assert errors[0].prop == 'padding'


def test_patch_padding_assignment_to_custom_real_property() -> None:
    assert patch_line_for_error('        padding: 8', 'padding') == '        property real padding: 8'
    assert patch_line_for_error('        padding: root.gap // keep', 'padding') == '        property real padding: root.gap // keep'


def test_patch_file_line_preserves_value(tmp_path: Path) -> None:
    root = tmp_path
    qml = root / 'src' / 'notizen_py_qt' / 'ui' / 'Main.qml'
    qml.parent.mkdir(parents=True)
    qml.write_text('import QtQuick\nItem {\n    padding: 12\n}\n', encoding='utf-8')
    backup = root / '.backup'
    action = patch_file_line(qml, 3, 'padding', root, backup, apply=True)
    assert action is not None
    assert 'property real padding: 12' in qml.read_text(encoding='utf-8')
    assert (backup / 'src' / 'notizen_py_qt' / 'ui' / 'Main.qml').exists()
