#!/usr/bin/env python3
"""
Best-effort Slint -> Qt 6.11 QML transpiler.

This is a project migration tool, not a formal Slint compiler. It converts the
parts of Slint UI code that can be translated mechanically into editable Qt
Quick/QML files and records lossy/ambiguous conversions as warnings plus
`// TODO(qt611-port): ...` comments.

v3 covers more than the initial line-based converter:

- component declarations -> one QML file per component
- exported globals -> QML singleton QtObject files
- top-level structs/enums -> Qt611Types.js helper library
- Window/AppWindow/Dialog -> Qt Quick Controls window/dialog types
- Vertical/Horizontal/Grid layouts -> Qt Quick Layouts
- standard widgets -> Qt Quick Controls
- Slint properties/callbacks/functions -> QML properties/signals/functions
- named child objects (`name := Type {`) -> QML `id: name`
- event handlers (`clicked => {`) -> QML handlers (`onClicked: {`)
- simple `for` and `if` object sugar -> Repeater/visible delegates
- simple animation blocks -> QML Behavior/NumberAnimation blocks
- two-way bindings (`foo <=> bar.baz`) -> QML binding + reverse handler when safe

Unsupported or ambiguous constructs are preserved as TODO comments so generated
QML remains reviewable instead of silently dropping behavior.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator, Optional

TYPE_MAP: dict[str, str] = {
    # containers/windows
    "Window": "ApplicationWindow",
    "AppWindow": "ApplicationWindow",
    "Dialog": "Dialog",
    "PopupWindow": "Popup",
    "ComponentContainer": "Item",
    "Item": "Item",
    "Rectangle": "Rectangle",
    "TouchArea": "MouseArea",
    "Flickable": "Flickable",
    "ScrollView": "ScrollView",
    "Viewport": "Flickable",
    "Clip": "Item",
    "FocusScope": "FocusScope",
    "QtObject": "QtObject",
    # layouts
    "VerticalBox": "ColumnLayout",
    "HorizontalBox": "RowLayout",
    "VerticalLayout": "ColumnLayout",
    "HorizontalLayout": "RowLayout",
    "GridLayout": "GridLayout",
    "GridBox": "GridLayout",
    # text/input/widgets
    "Text": "Text",
    "TextInput": "TextInput",
    "LineEdit": "TextField",
    "TextEdit": "TextArea",
    "Button": "Button",
    "CheckBox": "CheckBox",
    "SpinBox": "SpinBox",
    "Slider": "Slider",
    "ComboBox": "ComboBox",
    "ListView": "ListView",
    "StandardListView": "ListView",
    "Image": "Image",
    "Path": "ShapePath",
    "ProgressIndicator": "BusyIndicator",
    "ProgressBar": "ProgressBar",
    "GroupBox": "GroupBox",
    "TabWidget": "TabBar",
}

PROPERTY_MAP: dict[str, str] = {
    "background": "color",
    "background-color": "color",
    "border-color": "border.color",
    "border-width": "border.width",
    "border-radius": "radius",
    "font-size": "font.pixelSize",
    "font-weight": "font.weight",
    "font-family": "font.family",
    "horizontal-alignment": "horizontalAlignment",
    "vertical-alignment": "verticalAlignment",
    "alignment": "horizontalAlignment",
    "horizontal-stretch": "Layout.fillWidth",
    "vertical-stretch": "Layout.fillHeight",
    "min-width": "Layout.minimumWidth",
    "min-height": "Layout.minimumHeight",
    "max-width": "Layout.maximumWidth",
    "max-height": "Layout.maximumHeight",
    "preferred-width": "Layout.preferredWidth",
    "preferred-height": "Layout.preferredHeight",
    "col": "Layout.column",
    "row": "Layout.row",
    "colspan": "Layout.columnSpan",
    "rowspan": "Layout.rowSpan",
    "spacing": "spacing",
    "padding": "padding",
    "padding-left": "leftPadding",
    "padding-right": "rightPadding",
    "padding-top": "topPadding",
    "padding-bottom": "bottomPadding",
    "image-fit": "fillMode",
    "source": "source",
    "enabled": "enabled",
    "visible": "visible",
    "opacity": "opacity",
    "checked": "checked",
    "pressed": "pressed",
    "text": "text",
    "placeholder-text": "placeholderText",
    "wrap": "wrapMode",
    "clip": "clip",
    "model": "model",
    "current-index": "currentIndex",
    "current-value": "currentValue",
    "value": "value",
    "minimum": "from",
    "maximum": "to",
}

EVENT_MAP: dict[str, str] = {
    "clicked": "onClicked",
    "pressed": "onPressed",
    "released": "onReleased",
    "toggled": "onToggled",
    "accepted": "onAccepted",
    "rejected": "onRejected",
    "edited": "onEditingFinished",
    "editing-finished": "onEditingFinished",
    "changed": "onTextChanged",
    "text-changed": "onTextChanged",
    "activated": "onActivated",
    "current-index-changed": "onCurrentIndexChanged",
    "value-changed": "onValueChanged",
    "pointer-event": "onClicked",  # lossy; report emitted
    "touch-event": "onClicked",    # lossy; report emitted
    "key-pressed": "Keys.onPressed",
}

TYPE_QML_IMPORT_HINTS: dict[str, str] = {
    "ApplicationWindow": "QtQuick.Controls",
    "Dialog": "QtQuick.Controls",
    "Popup": "QtQuick.Controls",
    "Button": "QtQuick.Controls",
    "CheckBox": "QtQuick.Controls",
    "SpinBox": "QtQuick.Controls",
    "Slider": "QtQuick.Controls",
    "ComboBox": "QtQuick.Controls",
    "TextField": "QtQuick.Controls",
    "TextArea": "QtQuick.Controls",
    "ScrollView": "QtQuick.Controls",
    "BusyIndicator": "QtQuick.Controls",
    "ProgressBar": "QtQuick.Controls",
    "GroupBox": "QtQuick.Controls",
    "TabBar": "QtQuick.Controls",
    "ColumnLayout": "QtQuick.Layouts",
    "RowLayout": "QtQuick.Layouts",
    "GridLayout": "QtQuick.Layouts",
    "ShapePath": "QtQuick.Shapes",
    "QtObject": "QtQml",
}

SLINT_TYPE_TO_QML_TYPE: dict[str, str] = {
    "string": "string",
    "str": "string",
    "int": "int",
    "float": "double",
    "double": "double",
    "bool": "bool",
    "boolean": "bool",
    "brush": "color",
    "color": "color",
    "image": "url",
    "length": "real",
    "duration": "int",
    "angle": "real",
    "physical-length": "real",
    "relative-font-size": "real",
    "model": "var",
    "array": "var",
}

COMPONENT_RE = re.compile(
    r"^\s*(?P<export>export\s+)?component\s+(?P<name>[A-Za-z_][\w-]*)\s*(?:inherits\s+(?P<base>[A-Za-z_][\w-]*))?\s*\{\s*$"
)
GLOBAL_INLINE_RE = re.compile(r"^\s*(?P<export>export\s+)?global\s+(?P<name>[A-Za-z_][\w-]*)\s*\{\s*(?P<body>.*)\s*\}\s*;?\s*$")
GLOBAL_RE = re.compile(r"^\s*(?P<export>export\s+)?global\s+(?P<name>[A-Za-z_][\w-]*)\s*\{\s*$")
ENUM_RE = re.compile(r"^\s*(?P<export>export\s+)?enum\s+(?P<name>[A-Za-z_][\w-]*)\s*\{(?P<tail>.*)$")
STRUCT_RE = re.compile(r"^\s*(?P<export>export\s+)?struct\s+(?P<name>[A-Za-z_][\w-]*)\s*\{(?P<tail>.*)$")
GLOBAL_REEXPORT_RE = re.compile(r"^\s*export\s+\{.*\}\s*;?\s*$")
IMPORT_RE = re.compile(r"^\s*import\s+\{?(?P<body>[^}]*)\}?\s+from\s+['\"](?P<path>[^'\"]+)['\"]\s*;?\s*$")
PROPERTY_RE = re.compile(
    r"^\s*(?:(?P<direction>in|out|in-out)\s+)?property\s*<(?P<type>[^>]+)>\s+(?P<name>[A-Za-z_][\w-]*)\s*(?:(?P<op><=>|=>|:=|:)\s*(?P<value>.*?))?\s*;?\s*$"
)
CALLBACK_RE = re.compile(
    r"^\s*callback\s+(?P<name>[A-Za-z_][\w-]*)\s*\((?P<args>[^)]*)\)\s*(?:->\s*(?P<ret>[^;{]+))?\s*;?\s*$"
)
FUNCTION_RE = re.compile(
    r"^\s*(?:public\s+)?function\s+(?P<name>[A-Za-z_][\w-]*)\s*\((?P<args>[^)]*)\)\s*(?:->\s*(?P<ret>[^\s{]+))?\s*\{\s*$"
)
NAMED_OBJECT_RE = re.compile(r"^\s*(?P<id>[A-Za-z_][\w-]*)\s*:=\s*(?P<type>[A-Za-z_][\w-]*)\s*\{\s*$")
OBJECT_RE = re.compile(r"^\s*(?P<type>[A-Za-z_][\w-]*)\s*\{\s*$")
INLINE_OBJECT_RE = re.compile(r"^\s*(?:(?P<id>[A-Za-z_][\w-]*)\s*:=\s*)?(?P<type>[A-Za-z_][\w-]*)\s*\{\s*(?P<body>.*)\s*\}\s*;?\s*$")
IF_OBJECT_RE = re.compile(r"^\s*if\s+(?P<cond>.+?)\s*:\s*(?P<type>[A-Za-z_][\w-]*)\s*\{\s*$")
FOR_OBJECT_RE = re.compile(
    r"^\s*for\s+(?P<var>[A-Za-z_][\w-]*)(?:\[(?P<idx>[A-Za-z_][\w-]*)\])?\s+in\s+(?P<model>.+?)\s*:\s*(?P<type>[A-Za-z_][\w-]*)\s*\{\s*$"
)
IF_INLINE_OBJECT_RE = re.compile(r"^\s*if\s+(?P<cond>.+?)\s*:\s*(?P<type>[A-Za-z_][\w-]*)\s*\{\s*(?P<body>.*)\s*\}\s*;?\s*$")
FOR_INLINE_OBJECT_RE = re.compile(r"^\s*for\s+(?P<var>[A-Za-z_][\w-]*)(?:\[(?P<idx>[A-Za-z_][\w-]*)\])?\s+in\s+(?P<model>.+?)\s*:\s*(?P<type>[A-Za-z_][\w-]*)\s*\{\s*(?P<body>.*)\s*\}\s*;?\s*$")
EVENT_RE = re.compile(r"^\s*(?P<event>[A-Za-z_][\w-]*)\s*=>\s*(?P<body>.*)$")
TWO_WAY_BINDING_RE = re.compile(r"^\s*(?P<name>[A-Za-z_][\w.-]*)\s*<=>\s*(?P<value>.*?);?\s*$")
ONE_WAY_BINDING_RE = re.compile(r"^\s*(?P<name>[A-Za-z_][\w.-]*)\s*=>\s*(?P<value>.*?);?\s*$")
BINDING_RE = re.compile(r"^\s*(?P<name>[A-Za-z_][\w-]*)\s*:\s*(?P<value>.*?);?\s*$")
ANIMATE_RE = re.compile(r"^\s*animate\s+(?P<prop>[A-Za-z_][\w.-]*)\s*\{\s*$")
ANIMATE_INLINE_RE = re.compile(r"^\s*animate\s+(?P<prop>[A-Za-z_][\w.-]*)\s*\{\s*(?P<body>.*)\s*\}\s*;?\s*$")

UNSUPPORTED_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^\s*states\s*\["), "Slint states need manual QML State/Transition conversion"),
    (re.compile(r"^\s*@children\b"), "@children placeholder needs manual default-property handling"),
]


@dataclass
class TranspileWarning:
    line: int
    message: str
    source: str


@dataclass
class Component:
    name: str
    base: str
    exported: bool
    source_line: int
    body_lines: list[tuple[int, str]] = field(default_factory=list)


@dataclass
class GlobalBlock:
    name: str
    exported: bool
    source_line: int
    body_lines: list[tuple[int, str]] = field(default_factory=list)


@dataclass
class EnumDecl:
    name: str
    values: list[tuple[str, Optional[str]]]
    exported: bool
    source_line: int


@dataclass
class StructDecl:
    name: str
    fields: list[tuple[str, str, Optional[str]]]
    exported: bool
    source_line: int


@dataclass
class TranspileResult:
    source: str
    outputs: dict[str, str]
    warnings: list[TranspileWarning]
    imports: list[str]
    units: dict[str, int] = field(default_factory=dict)

    def to_report(self) -> dict[str, object]:
        return {
            "source": self.source,
            "outputs": sorted(self.outputs),
            "imports": self.imports,
            "units": self.units,
            "warnings": [warning.__dict__ for warning in self.warnings],
        }


def strip_line_comment(line: str) -> tuple[str, str]:
    in_single = False
    in_double = False
    escaped = False
    for idx in range(len(line) - 1):
        ch = line[idx]
        nxt = line[idx + 1]
        if escaped:
            escaped = False
            continue
        if ch == "\\":
            escaped = True
            continue
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == "/" and nxt == "/" and not in_single and not in_double:
            return line[:idx].rstrip(), line[idx:].rstrip()
    return line.rstrip(), ""


def camel_case(name: str) -> str:
    if "-" not in name:
        return name
    first, *rest = name.split("-")
    return first + "".join(part[:1].upper() + part[1:] for part in rest if part)


def upper_camel(name: str) -> str:
    ident = qml_member_identifier(name)
    return ident[:1].upper() + ident[1:] if ident else ident


def map_type(type_name: str) -> str:
    return TYPE_MAP.get(type_name, type_name)


def map_property(name: str) -> str:
    return PROPERTY_MAP.get(name, camel_case(name))


def map_slint_type(type_text: str) -> str:
    clean = type_text.strip().lower()
    if clean.startswith("[") and clean.endswith("]"):
        return "var"
    if clean.startswith("model<") or clean.startswith("model["):
        return "var"
    return SLINT_TYPE_TO_QML_TYPE.get(clean, "var")


def default_qml_value_for_slint_type(type_text: str) -> str:
    clean = type_text.strip().lower()
    if clean in {"string", "str"}:
        return '""'
    if clean in {"int", "float", "double", "length", "duration", "angle", "physical-length", "relative-font-size"}:
        return "0"
    if clean in {"bool", "boolean"}:
        return "false"
    if clean in {"brush", "color"}:
        return '"transparent"'
    if clean in {"image"}:
        return '""'
    if clean.startswith("[") or clean.startswith("model"):
        return "[]"
    return "null"


def normalize_identifier(name: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9_]", "_", name)
    if normalized and normalized[0].isdigit():
        normalized = "_" + normalized
    return normalized


def qml_member_identifier(name: str) -> str:
    return normalize_identifier(camel_case(name))


def normalize_reference_member(match: re.Match[str]) -> str:
    return match.group(1) + qml_member_identifier(match.group(2))


def normalize_references(expr: str) -> str:
    expr = re.sub(r"\bself\.", "root.", expr)
    # Convert obj.kebab-name and root.kebab-name to JS-compatible member access.
    return re.sub(r"(\b[A-Za-z_][A-Za-z0-9_]*\.)([A-Za-z_][\w-]*-[A-Za-z0-9_-]*)", normalize_reference_member, expr)


def split_top_level_semicolons(text: str) -> list[str]:
    parts: list[str] = []
    start = 0
    depth = 0
    in_single = False
    in_double = False
    escaped = False
    for idx, ch in enumerate(text):
        if escaped:
            escaped = False
            continue
        if ch == "\\":
            escaped = True
            continue
        if ch == "'" and not in_double:
            in_single = not in_single
            continue
        if ch == '"' and not in_single:
            in_double = not in_double
            continue
        if in_single or in_double:
            continue
        if ch in "({[":
            depth += 1
        elif ch in ")}]" and depth > 0:
            depth -= 1
        elif ch == ";" and depth == 0:
            part = text[start:idx].strip()
            if part:
                parts.append(part)
            start = idx + 1
    tail = text[start:].strip()
    if tail:
        parts.append(tail)
    return parts


def split_top_level_commas(text: str) -> list[str]:
    parts: list[str] = []
    start = 0
    depth = 0
    in_single = False
    in_double = False
    escaped = False
    for idx, ch in enumerate(text):
        if escaped:
            escaped = False
            continue
        if ch == "\\":
            escaped = True
            continue
        if ch == "'" and not in_double:
            in_single = not in_single
            continue
        if ch == '"' and not in_single:
            in_double = not in_double
            continue
        if in_single or in_double:
            continue
        if ch in "({[":
            depth += 1
        elif ch in ")}]" and depth > 0:
            depth -= 1
        elif ch == "," and depth == 0:
            part = text[start:idx].strip()
            if part:
                parts.append(part)
            start = idx + 1
    tail = text[start:].strip()
    if tail:
        parts.append(tail)
    return parts


def normalize_value(value: str) -> str:
    value = value.strip()
    if not value:
        return value
    value = value[:-1].rstrip() if value.endswith(";") else value

    value = re.sub(r"@tr\s*\(", "qsTr(", value)
    value = re.sub(r"@image-url\s*\(\s*(['\"])(.*?)\1\s*\)", r"\1\2\1", value)
    value = re.sub(r"\bdebug\s*\(", "console.log(", value)

    # Slint length/time units -> QML numeric pixel-ish values.
    value = re.sub(r"(?P<num>\b\d+(?:\.\d+)?)\s*(px|phx|pt|mm|cm|in|rem|em)", r"\g<num>", value)
    value = re.sub(r"(?P<num>\b\d+(?:\.\d+)?)\s*(ms)", r"\g<num>", value)
    value = re.sub(r"(?P<num>\b\d+(?:\.\d+)?)\s*s\b", lambda m: str(float(m.group("num")) * 1000).rstrip("0").rstrip("."), value)
    value = re.sub(r"(?P<num>\b\d+(?:\.\d+)?)\s*%", lambda m: str(float(m.group("num")) / 100.0).rstrip("0").rstrip("."), value)

    value = re.sub(r"(?<!['\"])(#[0-9A-Fa-f]{3,8})(?!['\"])", r'"\1"', value)

    replacements = {
        "center": "Text.AlignHCenter",
        "left": "Text.AlignLeft",
        "right": "Text.AlignRight",
        "top": "Text.AlignTop",
        "bottom": "Text.AlignBottom",
        "stretch": "Image.Stretch",
        "contain": "Image.PreserveAspectFit",
        "cover": "Image.PreserveAspectCrop",
        "no-wrap": "Text.NoWrap",
        "word-wrap": "Text.WordWrap",
    }
    if value in replacements:
        value = replacements[value]

    value = normalize_references(value)
    return value


def qml_signal_args(args: str) -> str:
    args = args.strip()
    if not args:
        return ""
    out: list[str] = []
    for index, raw in enumerate(args.split(",")):
        part = raw.strip()
        if not part:
            continue
        if ":" in part:
            name, typ = [x.strip() for x in part.split(":", 1)]
            out.append(f"{map_slint_type(typ)} {qml_member_identifier(name)}")
        else:
            words = part.split()
            if len(words) == 2:
                typ, name = words
                out.append(f"{map_slint_type(typ)} {qml_member_identifier(name)}")
            else:
                out.append(f"{map_slint_type(part)} arg{index}")
    return ", ".join(out)


def qml_function_args(args: str) -> str:
    args = args.strip()
    if not args:
        return ""
    out: list[str] = []
    for raw in args.split(","):
        part = raw.strip()
        if not part:
            continue
        name = part.split(":", 1)[0].strip() if ":" in part else part.split()[-1]
        out.append(qml_member_identifier(name))
    return ", ".join(out)


def count_open_braces(line: str) -> int:
    # This is intentionally rough; it is used for Slint block boundaries, not JS parsing.
    code, _ = strip_line_comment(line)
    return code.count("{") - code.count("}")


def is_assignable_reference(expr: str) -> bool:
    return bool(re.match(r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)+$", expr.strip()))


def is_aliasable_reference(expr: str) -> bool:
    return is_assignable_reference(expr) and len(expr.strip().split(".")) >= 2


def changed_handler_for_property(prop: str) -> Optional[str]:
    if "." in prop:
        return None
    ident = qml_member_identifier(prop)
    if not ident:
        return None
    return "on" + ident[:1].upper() + ident[1:] + "Changed"


def iter_source_files(path: Path) -> Iterator[Path]:
    if path.is_file():
        if path.suffix == ".slint":
            yield path
        return
    ignore = {".git", "target", "build", "legacy_slint", ".qt611_no_slint_backup", "node_modules", ".venv"}
    for dirpath, dirnames, filenames in os.walk(path):
        dirnames[:] = [d for d in dirnames if d not in ignore]
        for filename in filenames:
            if filename.endswith(".slint"):
                yield Path(dirpath) / filename


def _remove_outer_brace_payload(text: str) -> str:
    # Remove the final closing brace if present, then trim delimiters used in declarations.
    text = text.strip()
    if text.endswith("}"):
        text = text[:-1]
    return text.replace("{", " ").replace("}", " ").strip()


def parse_enum_values(raw_lines: list[str]) -> list[tuple[str, Optional[str]]]:
    text = _remove_outer_brace_payload("\n".join(raw_lines))
    text = re.sub(r"//.*", "", text)
    text = text.replace(";", ",").replace("\n", ",")
    values: list[tuple[str, Optional[str]]] = []
    for part in split_top_level_commas(text):
        part = part.strip().strip(",")
        if not part:
            continue
        if "=" in part:
            name, value = [x.strip() for x in part.split("=", 1)]
            values.append((qml_member_identifier(name), normalize_value(value)))
        else:
            values.append((qml_member_identifier(part), None))
    return values


def parse_struct_fields(raw_lines: list[str]) -> list[tuple[str, str, Optional[str]]]:
    text = _remove_outer_brace_payload("\n".join(raw_lines))
    text = re.sub(r"//.*", "", text)
    text = text.replace(";", ",").replace("\n", ",")
    fields: list[tuple[str, str, Optional[str]]] = []
    for part in split_top_level_commas(text):
        part = part.strip().strip(",")
        if not part or ":" not in part:
            continue
        name, rest = [x.strip() for x in part.split(":", 1)]
        default: Optional[str] = None
        if "=" in rest:
            typ, default = [x.strip() for x in rest.split("=", 1)]
        else:
            typ = rest
        fields.append((qml_member_identifier(name), typ, normalize_value(default) if default is not None else None))
    return fields


def extract_declarations(text: str, source_name: str) -> tuple[list[Component], list[GlobalBlock], list[EnumDecl], list[StructDecl], list[str], list[TranspileWarning]]:
    imports: list[str] = []
    warnings: list[TranspileWarning] = []
    components: list[Component] = []
    globals_: list[GlobalBlock] = []
    enums: list[EnumDecl] = []
    structs: list[StructDecl] = []

    current: Component | GlobalBlock | None = None
    current_kind: str | None = None
    depth = 0

    aggregate_kind: str | None = None
    aggregate_name = ""
    aggregate_exported = False
    aggregate_line = 0
    aggregate_lines: list[str] = []
    aggregate_depth = 0

    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        code, _comment = strip_line_comment(raw_line)
        stripped = code.strip()

        if aggregate_kind is not None:
            aggregate_lines.append(stripped)
            aggregate_depth += count_open_braces(code)
            if aggregate_depth <= 0:
                if aggregate_kind == "enum":
                    enums.append(EnumDecl(aggregate_name, parse_enum_values(aggregate_lines), aggregate_exported, aggregate_line))
                else:
                    structs.append(StructDecl(aggregate_name, parse_struct_fields(aggregate_lines), aggregate_exported, aggregate_line))
                aggregate_kind = None
                aggregate_lines = []
            continue

        if current is not None:
            delta = count_open_braces(code)
            if stripped in {"}", "};", "},"} and depth == 1:
                if current_kind == "component":
                    components.append(current)  # type: ignore[arg-type]
                else:
                    globals_.append(current)  # type: ignore[arg-type]
                current = None
                current_kind = None
                depth = 0
                continue
            current.body_lines.append((lineno, raw_line.rstrip()))
            depth += delta
            if depth <= 0:
                if current_kind == "component":
                    components.append(current)  # type: ignore[arg-type]
                else:
                    globals_.append(current)  # type: ignore[arg-type]
                current = None
                current_kind = None
                depth = 0
            continue

        if not stripped:
            continue

        m_import = IMPORT_RE.match(stripped)
        if m_import:
            imports.append(m_import.group("path"))
            continue

        if GLOBAL_REEXPORT_RE.match(stripped):
            continue

        m_comp = COMPONENT_RE.match(stripped)
        if m_comp:
            current = Component(
                name=normalize_identifier(m_comp.group("name")),
                base=m_comp.group("base") or "Item",
                exported=bool(m_comp.group("export")),
                source_line=lineno,
            )
            current_kind = "component"
            depth = 1
            continue

        m_global_inline = GLOBAL_INLINE_RE.match(stripped)
        if m_global_inline:
            body = m_global_inline.group("body").strip()
            block = GlobalBlock(
                name=normalize_identifier(m_global_inline.group("name")),
                exported=bool(m_global_inline.group("export")),
                source_line=lineno,
            )
            block.body_lines = [(lineno, part + ";") for part in split_top_level_semicolons(body)]
            globals_.append(block)
            continue

        m_global = GLOBAL_RE.match(stripped)
        if m_global:
            current = GlobalBlock(
                name=normalize_identifier(m_global.group("name")),
                exported=bool(m_global.group("export")),
                source_line=lineno,
            )
            current_kind = "global"
            depth = 1
            continue

        m_enum = ENUM_RE.match(stripped)
        if m_enum:
            aggregate_kind = "enum"
            aggregate_name = normalize_identifier(m_enum.group("name"))
            aggregate_exported = bool(m_enum.group("export"))
            aggregate_line = lineno
            aggregate_lines = [m_enum.group("tail")]
            aggregate_depth = count_open_braces(code)
            if aggregate_depth <= 0:
                enums.append(EnumDecl(aggregate_name, parse_enum_values(aggregate_lines), aggregate_exported, aggregate_line))
                aggregate_kind = None
                aggregate_lines = []
            continue

        m_struct = STRUCT_RE.match(stripped)
        if m_struct:
            aggregate_kind = "struct"
            aggregate_name = normalize_identifier(m_struct.group("name"))
            aggregate_exported = bool(m_struct.group("export"))
            aggregate_line = lineno
            aggregate_lines = [m_struct.group("tail")]
            aggregate_depth = count_open_braces(code)
            if aggregate_depth <= 0:
                structs.append(StructDecl(aggregate_name, parse_struct_fields(aggregate_lines), aggregate_exported, aggregate_line))
                aggregate_kind = None
                aggregate_lines = []
            continue

        warnings.append(TranspileWarning(lineno, "Top-level Slint construct not converted", raw_line.strip()))

    if current is not None:
        warnings.append(TranspileWarning(current.source_line, f"Unclosed {current_kind}; converted best effort", current.name))
        if current_kind == "component":
            components.append(current)  # type: ignore[arg-type]
        else:
            globals_.append(current)  # type: ignore[arg-type]

    if aggregate_kind is not None:
        warnings.append(TranspileWarning(aggregate_line, f"Unclosed {aggregate_kind}; converted best effort", aggregate_name))
        if aggregate_kind == "enum":
            enums.append(EnumDecl(aggregate_name, parse_enum_values(aggregate_lines), aggregate_exported, aggregate_line))
        else:
            structs.append(StructDecl(aggregate_name, parse_struct_fields(aggregate_lines), aggregate_exported, aggregate_line))

    if not components and not globals_ and text.strip():
        comp = Component("Main", "Window", True, 1)
        comp.body_lines = list(enumerate(text.splitlines(), start=1))
        components.append(comp)
        warnings.append(TranspileWarning(1, "No component/global declaration found; wrapped file as Main.qml", source_name))

    return components, globals_, enums, structs, imports, warnings


class BodyTranspiler:
    def __init__(self) -> None:
        self.warnings: list[TranspileWarning] = []
        self.used_types: set[str] = set()
        self.indent = 1
        # Number of QML braces that correspond to each single Slint source block.
        # This fixes constructs like `for x in xs: Text { ... }`, which opens
        # both a Repeater and a delegate in QML but has one Slint closing brace.
        self.source_block_close_counts: list[int] = []

    def q(self, text: str = "", extra_indent: int = 0) -> str:
        return "    " * max(0, self.indent + extra_indent) + text

    def warn(self, lineno: int, message: str, source: str) -> None:
        self.warnings.append(TranspileWarning(lineno, message, source.strip()))

    def emit_object_open(self, qml_type: str, object_id: Optional[str] = None, extra: list[str] | None = None) -> list[str]:
        self.used_types.add(qml_type)
        out = [self.q(f"{qml_type} {{")]
        self.indent += 1
        self.source_block_close_counts.append(1)
        if object_id:
            out.append(self.q(f"id: {normalize_identifier(object_id)}"))
        if extra:
            out.extend(self.q(x) for x in extra)
        return out

    def close_block(self) -> list[str]:
        self.indent = max(0, self.indent - 1)
        return [self.q("}")]

    def close_source_block(self) -> list[str]:
        count = self.source_block_close_counts.pop() if self.source_block_close_counts else 1
        out: list[str] = []
        for _ in range(count):
            out.extend(self.close_block())
        return out

    def transform_binding(self, lineno: int, name: str, value: str, op: str = ":") -> list[str]:
        prop = map_property(name)
        normalized = normalize_value(value)
        if prop in {"Layout.fillWidth", "Layout.fillHeight"}:
            if normalized and normalized not in {"0", "false"}:
                return [self.q(f"{prop}: true  // from {name}: {normalized}")]
            return [self.q(f"{prop}: false")]
        if op == "<=>":
            out = [self.q(f"{prop}: {normalized}")]
            handler = changed_handler_for_property(prop)
            if handler and is_assignable_reference(normalized):
                out.append(self.q(f"{handler}: {{ {normalized} = {prop} }}"))
                self.warn(lineno, "Two-way binding converted to QML binding plus reverse change handler; check for binding loops", f"{name} <=> {value}")
            else:
                out.append(self.q(f"// TODO(qt611-port): reverse side of two-way binding needs manual port: {name} <=> {normalized}"))
                self.warn(lineno, "Two-way binding needs manual reverse update", f"{name} <=> {value}")
            return out
        return [self.q(f"{prop}: {normalized}")]

    def transform_event(self, lineno: int, event: str, body: str) -> list[str]:
        mapped = EVENT_MAP.get(event, "on" + upper_camel(event))
        if event in {"pointer-event", "touch-event"}:
            self.warn(lineno, f"{event} was mapped to {mapped}; pointer details need manual porting", body)
        body = normalize_references(body.strip())
        if body == "{":
            out = [self.q(f"{mapped}: {{")]
            self.indent += 1
            self.source_block_close_counts.append(1)
            return out
        if body.startswith("{") and body.endswith("}"):
            return [self.q(f"{mapped}: {normalize_value(body)}")]
        return [self.q(f"{mapped}: {normalize_value(body)}")]

    def transform_property_declaration(self, lineno: int, raw_line: str, match: re.Match[str]) -> list[str]:
        qml_type = map_slint_type(match.group("type"))
        name = qml_member_identifier(match.group("name"))
        value = match.group("value")
        op = match.group("op") or ""
        direction = match.group("direction") or "in-out"
        if op == "<=>" and value is not None and is_aliasable_reference(normalize_value(value)):
            return [self.q(f"property alias {name}: {normalize_value(value)}")]
        prefix = "readonly property" if direction == "out" or op == "=>" else "property"
        if value is not None and value.strip():
            line = f"{prefix} {qml_type} {name}: {normalize_value(value)}"
            if op == "<=>":
                self.warn(lineno, "Property two-way binding could not become alias; emitted one-way initial binding", raw_line)
                return [self.q(line), self.q(f"// TODO(qt611-port): verify two-way property binding from: {raw_line.strip()}")]
            return [self.q(line)]
        return [self.q(f"{prefix} {qml_type} {name}")]

    def transform_inline_body(self, lineno: int, body: str) -> list[str]:
        out: list[str] = []
        for part in split_top_level_semicolons(body):
            part = part.strip()
            if not part:
                continue
            m_event = EVENT_RE.match(part)
            if m_event:
                out.extend(self.transform_event(lineno, m_event.group("event"), m_event.group("body")))
                continue
            m_two = TWO_WAY_BINDING_RE.match(part)
            if m_two:
                out.extend(self.transform_binding(lineno, m_two.group("name"), m_two.group("value"), op="<=>"))
                continue
            m_one = ONE_WAY_BINDING_RE.match(part)
            if m_one:
                out.extend(self.transform_binding(lineno, m_one.group("name"), m_one.group("value"), op="=>"))
                continue
            m_binding = BINDING_RE.match(part)
            if m_binding:
                out.extend(self.transform_binding(lineno, m_binding.group("name"), m_binding.group("value")))
                continue
            out.append(self.q(f"// TODO(qt611-port): {normalize_references(part)}"))
            self.warn(lineno, "Inline statement needs manual conversion", part)
        return out

    def transform_inline_object(self, lineno: int, qml_type: str, body: str, object_id: Optional[str] = None) -> list[str]:
        out = self.emit_object_open(qml_type, object_id=object_id)
        # Inline object does not correspond to a future source closing brace.
        if self.source_block_close_counts:
            self.source_block_close_counts.pop()
        out.extend(self.transform_inline_body(lineno, body))
        out.extend(self.close_block())
        return out

    def transform_for_object(self, lineno: int, var: str, idx: Optional[str], model: str, typ: str) -> list[str]:
        qml_type = map_type(typ)
        self.used_types.add("Repeater")
        self.used_types.add(qml_type)
        normalized_model = normalize_value(model)
        out = [self.q("Repeater {"), self.q(f"model: {normalized_model}", 1), self.q(f"delegate: {qml_type} {{", 1)]
        self.indent += 2
        self.source_block_close_counts.append(2)
        out.append(self.q(f"property var {normalize_identifier(var)}: modelData"))
        if idx:
            out.append(self.q(f"property int {normalize_identifier(idx)}: index"))
        self.warn(lineno, "Slint for-loop converted to Repeater; check model roles and delegate sizing", f"for {var} in {model}: {typ}")
        return out

    def transform_animate_inline(self, lineno: int, prop: str, body: str) -> list[str]:
        mapped_prop = map_property(prop)
        self.used_types.add("NumberAnimation")
        self.warn(lineno, "Slint animate block converted to QML Behavior/NumberAnimation; easing may need review", f"animate {prop}")
        out = [self.q(f"Behavior on {mapped_prop} {{")]
        self.indent += 1
        out.append(self.q("NumberAnimation {"))
        self.indent += 1
        out.extend(self.transform_inline_body(lineno, body))
        out.extend(self.close_block())
        out.extend(self.close_block())
        return out

    def transform_animate_open(self, lineno: int, prop: str) -> list[str]:
        mapped_prop = map_property(prop)
        self.used_types.add("NumberAnimation")
        self.warn(lineno, "Slint animate block converted to QML Behavior/NumberAnimation; easing may need review", f"animate {prop}")
        out = [self.q(f"Behavior on {mapped_prop} {{")]
        self.indent += 1
        out.append(self.q("NumberAnimation {"))
        self.indent += 1
        self.source_block_close_counts.append(2)
        return out

    def transform_line(self, lineno: int, raw_line: str) -> list[str]:
        code, comment = strip_line_comment(raw_line)
        stripped = code.strip()
        if not stripped:
            return [self.q(comment) if comment else ""]

        if stripped in {"}", "};", "},"}:
            return self.close_source_block()

        for pattern, message in UNSUPPORTED_PATTERNS:
            if pattern.match(stripped):
                self.warn(lineno, message, raw_line)
                return [self.q(f"// TODO(qt611-port): {message}: {stripped}")]

        m_animate_inline = ANIMATE_INLINE_RE.match(stripped)
        if m_animate_inline:
            return self.transform_animate_inline(lineno, m_animate_inline.group("prop"), m_animate_inline.group("body"))

        m_animate = ANIMATE_RE.match(stripped)
        if m_animate:
            return self.transform_animate_open(lineno, m_animate.group("prop"))

        m_for_inline = FOR_INLINE_OBJECT_RE.match(stripped)
        if m_for_inline:
            out = self.transform_for_object(
                lineno,
                m_for_inline.group("var"),
                m_for_inline.group("idx"),
                m_for_inline.group("model"),
                m_for_inline.group("type"),
            )
            # It is inline, so close the source-block mapping ourselves.
            if self.source_block_close_counts:
                self.source_block_close_counts.pop()
            out.extend(self.transform_inline_body(lineno, m_for_inline.group("body")))
            out.extend(self.close_block())
            out.extend(self.close_block())
            return out

        m_if_inline = IF_INLINE_OBJECT_RE.match(stripped)
        if m_if_inline:
            cond = normalize_value(m_if_inline.group("cond"))
            qml_type = map_type(m_if_inline.group("type"))
            self.warn(lineno, "Slint conditional object converted to always-created QML item with visible binding", raw_line)
            out = self.emit_object_open(qml_type, extra=[f"visible: {cond}"])
            if self.source_block_close_counts:
                self.source_block_close_counts.pop()
            out.extend(self.transform_inline_body(lineno, m_if_inline.group("body")))
            out.extend(self.close_block())
            return out

        m_inline = INLINE_OBJECT_RE.match(stripped)
        if m_inline:
            qml_type = map_type(m_inline.group("type"))
            return self.transform_inline_object(lineno, qml_type, m_inline.group("body"), m_inline.group("id"))

        m_prop = PROPERTY_RE.match(stripped)
        if m_prop:
            return self.transform_property_declaration(lineno, raw_line, m_prop)

        m_callback = CALLBACK_RE.match(stripped)
        if m_callback:
            name = qml_member_identifier(m_callback.group("name"))
            args = qml_signal_args(m_callback.group("args"))
            if m_callback.group("ret"):
                self.warn(lineno, "QML signals do not return values; callback return type dropped", raw_line)
            return [self.q(f"signal {name}({args})")]

        m_function = FUNCTION_RE.match(stripped)
        if m_function:
            name = qml_member_identifier(m_function.group("name"))
            args = qml_function_args(m_function.group("args"))
            out = [self.q(f"function {name}({args}) {{")]
            self.indent += 1
            self.source_block_close_counts.append(1)
            return out

        m_for = FOR_OBJECT_RE.match(stripped)
        if m_for:
            return self.transform_for_object(lineno, m_for.group("var"), m_for.group("idx"), m_for.group("model"), m_for.group("type"))

        m_if = IF_OBJECT_RE.match(stripped)
        if m_if:
            cond = normalize_value(m_if.group("cond"))
            qml_type = map_type(m_if.group("type"))
            self.warn(lineno, "Slint conditional object converted to always-created QML item with visible binding", raw_line)
            return self.emit_object_open(qml_type, extra=[f"visible: {cond}"])

        m_named = NAMED_OBJECT_RE.match(stripped)
        if m_named:
            qml_type = map_type(m_named.group("type"))
            return self.emit_object_open(qml_type, object_id=m_named.group("id"))

        m_object = OBJECT_RE.match(stripped)
        if m_object:
            qml_type = map_type(m_object.group("type"))
            return self.emit_object_open(qml_type)

        m_event = EVENT_RE.match(stripped)
        if m_event:
            return self.transform_event(lineno, m_event.group("event"), m_event.group("body"))

        m_two = TWO_WAY_BINDING_RE.match(stripped)
        if m_two:
            return self.transform_binding(lineno, m_two.group("name"), m_two.group("value"), op="<=>")

        m_one = ONE_WAY_BINDING_RE.match(stripped)
        if m_one:
            return self.transform_binding(lineno, m_one.group("name"), m_one.group("value"), op="=>")

        m_binding = BINDING_RE.match(stripped)
        if m_binding:
            return self.transform_binding(lineno, m_binding.group("name"), m_binding.group("value"))

        # JS-like statements in handlers/functions mostly pass through.
        if stripped.endswith(";") or stripped.startswith(("let ", "return ", "if ", "for ", "while ")):
            return [self.q(normalize_value(stripped))]

        self.warn(lineno, "Line copied as TODO comment; manual conversion required", raw_line)
        return [self.q(f"// TODO(qt611-port): {normalize_references(stripped)}")]

    def transform_body(self, body_lines: list[tuple[int, str]]) -> tuple[list[str], list[TranspileWarning], set[str]]:
        out: list[str] = []
        for lineno, line in body_lines:
            out.extend(self.transform_line(lineno, line))
        while self.indent > 1:
            self.indent -= 1
            out.append(self.q("}"))
        return out, self.warnings, self.used_types


def build_imports(used_types: set[str]) -> list[str]:
    imports = ["import QtQuick", "import QtQuick.Controls", "import QtQuick.Layouts"]
    if any(TYPE_QML_IMPORT_HINTS.get(t) == "QtQuick.Shapes" for t in used_types):
        imports.append("import QtQuick.Shapes")
    if any(TYPE_QML_IMPORT_HINTS.get(t) == "QtQml" for t in used_types):
        imports.append("import QtQml")
    return imports


def qml_component_text(component: Component) -> tuple[str, list[TranspileWarning], set[str]]:
    qml_type = map_type(component.base)
    body_transpiler = BodyTranspiler()
    body_transpiler.used_types.add(qml_type)
    body_lines, warnings, used_types = body_transpiler.transform_body(component.body_lines)
    imports = build_imports(used_types)

    lines: list[str] = []
    lines.extend(imports)
    lines.append("")
    lines.append(f"{qml_type} {{")
    lines.append("    id: root")
    if qml_type == "ApplicationWindow":
        if not any(re.match(r"^    visible\s*:", line) for line in body_lines):
            lines.append("    visible: true")
    lines.extend(body_lines)
    lines.append("}")
    lines.append("")
    return "\n".join(lines), warnings, used_types


def qml_global_text(global_block: GlobalBlock) -> tuple[str, list[TranspileWarning], set[str]]:
    body_transpiler = BodyTranspiler()
    body_transpiler.used_types.add("QtObject")
    body_lines, warnings, used_types = body_transpiler.transform_body(global_block.body_lines)
    lines = [
        "pragma Singleton",
        "import QtQml",
        "",
        "QtObject {",
        "    id: root",
    ]
    lines.extend(body_lines)
    lines.append("}")
    lines.append("")
    return "\n".join(lines), warnings, used_types


def js_types_text(enums: list[EnumDecl], structs: list[StructDecl]) -> str:
    lines: list[str] = [
        ".pragma library",
        "",
        "// Generated helper library for migrated enum/struct declarations.",
        "// Review usages and replace with typed C++/Rust/QML models where needed.",
        "",
    ]
    for enum in enums:
        lines.append(f"var {normalize_identifier(enum.name)} = Object.freeze({{")
        for index, (name, value) in enumerate(enum.values):
            comma = "," if index < len(enum.values) - 1 else ""
            enum_value = value if value is not None else str(index)
            lines.append(f"    {normalize_identifier(name)}: {enum_value}{comma}")
        lines.append("});")
        lines.append("")
    for struct in structs:
        factory = "make" + normalize_identifier(struct.name)
        lines.append(f"function {factory}(values) {{")
        lines.append("    values = values || {};")
        lines.append("    return {")
        for index, (field, typ, default) in enumerate(struct.fields):
            comma = "," if index < len(struct.fields) - 1 else ""
            default_value = default if default is not None else default_qml_value_for_slint_type(typ)
            lines.append(f"        {normalize_identifier(field)}: values.{normalize_identifier(field)} !== undefined ? values.{normalize_identifier(field)} : {default_value}{comma}")
        lines.append("    };")
        lines.append("}")
        lines.append("")
    return "\n".join(lines)


def generated_singletons_cmake(singleton_names: Iterable[str]) -> str:
    names = [normalize_identifier(name) for name in singleton_names]
    if not names:
        return ""
    lines = [
        "# Generated by migration tooling. Include before qt_add_qml_module().",
        "",
    ]
    for name in names:
        lines.extend([
            "set_source_files_properties(",
            f"    ${{CMAKE_CURRENT_SOURCE_DIR}}/qml/{name}.qml",
            "    PROPERTIES QT_QML_SINGLETON_TYPE TRUE",
            ")",
            "",
        ])
    return "\n".join(lines)


def transpile_text(text: str, source_name: str = "<memory>") -> TranspileResult:
    components, globals_, enums, structs, imports, warnings = extract_declarations(text, source_name)
    outputs: dict[str, str] = {}
    for component in components:
        qml_text, body_warnings, _used = qml_component_text(component)
        warnings.extend(body_warnings)
        outputs[f"{component.name}.qml"] = qml_text
    for global_block in globals_:
        qml_text, body_warnings, _used = qml_global_text(global_block)
        warnings.extend(body_warnings)
        outputs[f"{global_block.name}.qml"] = qml_text
    if enums or structs:
        outputs["Qt611Types.js"] = js_types_text(enums, structs)
    if globals_:
        outputs["GeneratedQmlSingletons.cmake"] = generated_singletons_cmake(g.name for g in globals_)
    return TranspileResult(
        source=source_name,
        outputs=outputs,
        warnings=warnings,
        imports=imports,
        units={
            "components": len(components),
            "globals": len(globals_),
            "enums": len(enums),
            "structs": len(structs),
        },
    )


def _main_alias_candidate(outputs: dict[str, str]) -> Optional[str]:
    preferred = ["Main.qml", "MainWindow.qml", "App.qml", "AppWindow.qml", "Window.qml"]
    for name in preferred:
        if name in outputs and not outputs[name].lstrip().startswith("pragma Singleton"):
            return name
    for name, text in outputs.items():
        if name.endswith(".qml") and not text.lstrip().startswith("pragma Singleton"):
            return name
    return None


def transpile_file(path: Path, out_dir: Path, *, overwrite: bool = False, main_alias: bool = True) -> TranspileResult:
    text = path.read_text(encoding="utf-8")
    result = transpile_text(text, str(path))
    out_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, str] = {}
    for name, content in result.outputs.items():
        if name.endswith(".cmake"):
            target = out_dir / name
        else:
            target = out_dir / name
        if target.exists() and not overwrite:
            stem = path.stem
            target = out_dir / f"{stem}_{name}"
        target.write_text(content, encoding="utf-8")
        written[target.name] = content

    if main_alias and "Main.qml" not in written:
        candidate = _main_alias_candidate(result.outputs)
        if candidate:
            main_target = out_dir / "Main.qml"
            if overwrite or not main_target.exists():
                main_target.write_text(result.outputs[candidate], encoding="utf-8")
                written["Main.qml"] = result.outputs[candidate]

    result.outputs = written
    report_path = out_dir / f"{path.stem}.slint_to_qml.report.json"
    report_path.write_text(json.dumps(result.to_report(), indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def transpile_path(path: Path, out_dir: Path, *, overwrite: bool = False, main_alias: bool = True) -> list[TranspileResult]:
    results: list[TranspileResult] = []
    for source in iter_source_files(path):
        results.append(transpile_file(source, out_dir, overwrite=overwrite, main_alias=main_alias))
    return results


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Best-effort Slint to Qt 6.11 QML transpiler")
    parser.add_argument("input", type=Path, help=".slint file or project directory")
    parser.add_argument("-o", "--out-dir", type=Path, default=Path("qml"), help="directory for generated QML/JS files")
    parser.add_argument("--overwrite", action="store_true", help="overwrite existing generated files")
    parser.add_argument("--no-main-alias", action="store_true", help="do not create Main.qml alias for obvious main windows")
    parser.add_argument("--json", action="store_true", help="print JSON report")
    args = parser.parse_args(argv)

    if not args.input.exists():
        print(f"ERROR: input not found: {args.input}", file=sys.stderr)
        return 2

    results = transpile_path(args.input, args.out_dir, overwrite=args.overwrite, main_alias=not args.no_main_alias)
    if not results:
        print(f"No .slint files found under {args.input}", file=sys.stderr)
        return 1

    report = [result.to_report() for result in results]
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"Transpiled {len(results)} Slint file(s) to {args.out_dir}")
        total_warnings = 0
        for result in results:
            total_warnings += len(result.warnings)
            print(f"- {result.source}: {', '.join(sorted(result.outputs))}")
            print(f"  units: {result.units}")
            for warning in result.warnings[:30]:
                print(f"  warning line {warning.line}: {warning.message}: {warning.source}")
            if len(result.warnings) > 30:
                print(f"  ... {len(result.warnings) - 30} more warnings")
        print(f"Warnings: {total_warnings}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
