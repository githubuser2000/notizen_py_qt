#!/usr/bin/env python3
"""
Best-effort Slint -> Qt 6.11 QML transpiler.

This is not a formal Slint compiler. It is a project migration tool that converts
common Slint declarative UI structures into editable Qt Quick/QML files:

- component declarations -> one QML file per exported component
- Window/AppWindow/Dialog -> Qt Quick Controls ApplicationWindow/Popup-ish types
- Vertical/Horizontal/Grid layouts -> Qt Quick Layouts
- standard widgets -> Qt Quick Controls
- Slint properties/callbacks -> QML properties/signals
- named child objects (`name := Type {`) -> QML `id: name`
- event handlers (`clicked => {`) -> QML handlers (`onClicked: {`)
- simple `for` and `if` object sugar -> Repeater/visible delegates

Unsupported or ambiguous constructs are preserved as comments prefixed with
`// TODO(slint->qml):` so the result remains reviewable.
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

# Direct type mappings from common Slint elements to QML/Qt Quick types.
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
    "Image": "Image",
    "Path": "ShapePath",
}

# Property mappings. Some Slint properties are direct camelCase conversions; some
# need semantic Qt names.
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
}

# Slint callbacks/events to QML signal handlers.
EVENT_MAP: dict[str, str] = {
    "clicked": "onClicked",
    "pressed": "onPressed",
    "released": "onReleased",
    "toggled": "onToggled",
    "accepted": "onAccepted",
    "edited": "onEditingFinished",
    "changed": "onTextChanged",
    "text-changed": "onTextChanged",
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
    "ColumnLayout": "QtQuick.Layouts",
    "RowLayout": "QtQuick.Layouts",
    "GridLayout": "QtQuick.Layouts",
    "ShapePath": "QtQuick.Shapes",
}

SLINT_TYPE_TO_QML_TYPE: dict[str, str] = {
    "string": "string",
    "str": "string",
    "int": "int",
    "float": "double",
    "double": "double",
    "bool": "bool",
    "brush": "color",
    "color": "color",
    "image": "url",
    "length": "real",
    "duration": "int",
    "angle": "real",
    "physical-length": "real",
    "relative-font-size": "real",
    "model": "var",
}

COMPONENT_RE = re.compile(
    r"^\s*(?P<export>export\s+)?component\s+(?P<name>[A-Za-z_][\w-]*)\s*(?:inherits\s+(?P<base>[A-Za-z_][\w-]*))?\s*\{\s*$"
)
GLOBAL_REEXPORT_RE = re.compile(r"^\s*export\s+\{.*\}\s*;?\s*$")
IMPORT_RE = re.compile(r"^\s*import\s+\{?(?P<body>[^}]*)\}?\s+from\s+['\"](?P<path>[^'\"]+)['\"]\s*;?\s*$")
PROPERTY_RE = re.compile(
    r"^\s*(?:(?P<direction>in|out|in-out)\s+)?property\s*<(?P<type>[^>]+)>\s+(?P<name>[A-Za-z_][\w-]*)\s*(?::\s*(?P<value>.*?))?\s*;?\s*$"
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
BINDING_RE = re.compile(r"^\s*(?P<name>[A-Za-z_][\w-]*)\s*:\s*(?P<value>.*?);?\s*$")
STATE_RE = re.compile(r"^\s*states\s*\[\s*$")
ANIMATE_RE = re.compile(r"^\s*animate\s+(?P<prop>[A-Za-z_][\w.-]*)\s*\{\s*$")

UNSUPPORTED_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^\s*states\s*\["), "Slint states need manual QML State/Transition conversion"),
    (re.compile(r"^\s*animate\s+"), "Slint animation block needs manual QML Behavior/Transition conversion"),
    (re.compile(r"^\s*@children\b"), "@children placeholder needs manual default property handling"),
    (re.compile(r"^\s*global\s+"), "Slint global singleton needs manual QML singleton/context-property mapping"),
    (re.compile(r"^\s*struct\s+"), "Slint struct declarations need manual JS/C++/Rust model mapping"),
    (re.compile(r"^\s*enum\s+"), "Slint enum declarations need manual QML enum mapping"),
]


def strip_line_comment(line: str) -> tuple[str, str]:
    """Return (code, comment) while respecting quoted strings roughly."""
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


def map_type(type_name: str) -> str:
    return TYPE_MAP.get(type_name, type_name)


def map_property(name: str) -> str:
    return PROPERTY_MAP.get(name, camel_case(name))


def map_slint_type(type_text: str) -> str:
    clean = type_text.strip().lower()
    # Slint models often look like [Foo] or [string]. QML can accept var.
    if clean.startswith("[") and clean.endswith("]"):
        return "var"
    return SLINT_TYPE_TO_QML_TYPE.get(clean, "var")


def normalize_identifier(name: str) -> str:
    # QML ids cannot contain hyphens.
    return re.sub(r"[^A-Za-z0-9_]", "_", name)


def qml_member_identifier(name: str) -> str:
    # QML property/signal/function names should be JavaScript identifiers. Slint
    # often uses kebab-case names; convert those to camelCase rather than
    # underscores so bindings read naturally in QML.
    return normalize_identifier(camel_case(name))


def normalize_references(expr: str) -> str:
    def repl(match: re.Match[str]) -> str:
        return match.group(1) + qml_member_identifier(match.group(2))

    return re.sub(r"(\b(?:root|self|parent)\.)([A-Za-z_][\w-]*-[A-Za-z0-9_-]*)", repl, expr)


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


def normalize_value(value: str) -> str:
    value = value.strip()
    if not value:
        return value

    # Remove trailing semicolon left by partial matches.
    value = value[:-1].rstrip() if value.endswith(";") else value

    # Slint length/time units -> QML numeric pixel-ish values. This is lossy for
    # physical units, but QML layouts need numbers.
    value = re.sub(r"(?P<num>\b\d+(?:\.\d+)?)\s*(px|phx|pt|mm|cm|in)", r"\g<num>", value)
    value = re.sub(r"(?P<num>\b\d+(?:\.\d+)?)\s*(ms)", r"\g<num>", value)
    value = re.sub(r"(?P<num>\b\d+(?:\.\d+)?)\s*s\b", lambda m: str(float(m.group("num")) * 1000).rstrip("0").rstrip("."), value)

    # Colors in Slint are often #rgb/#rrggbb tokens. QML accepts strings.
    value = re.sub(r"(?<!['\"])(#[0-9A-Fa-f]{3,8})(?!['\"])", r'"\1"', value)

    # Slint booleans match QML. Some enum-ish alignment values need Qt names.
    replacements = {
        "center": "Text.AlignHCenter",
        "left": "Text.AlignLeft",
        "right": "Text.AlignRight",
        "top": "Text.AlignTop",
        "bottom": "Text.AlignBottom",
        "stretch": "Image.Stretch",
        "contain": "Image.PreserveAspectFit",
        "cover": "Image.PreserveAspectCrop",
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
        # Slint may use `name: type`, `type`, or occasionally `type name`.
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
    return line.count("{") - line.count("}")


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
class TranspileResult:
    source: str
    outputs: dict[str, str]
    warnings: list[TranspileWarning]
    imports: list[str]

    def to_report(self) -> dict[str, object]:
        return {
            "source": self.source,
            "outputs": sorted(self.outputs),
            "imports": self.imports,
            "warnings": [warning.__dict__ for warning in self.warnings],
        }


def iter_source_files(path: Path) -> Iterator[Path]:
    if path.is_file():
        if path.suffix == ".slint":
            yield path
        return
    ignore = {".git", "target", "build", "legacy_slint", ".qt611_no_slint_backup", "node_modules"}
    for dirpath, dirnames, filenames in os.walk(path):
        dirnames[:] = [d for d in dirnames if d not in ignore]
        for filename in filenames:
            if filename.endswith(".slint"):
                yield Path(dirpath) / filename


def extract_components(text: str, source_name: str) -> tuple[list[Component], list[str], list[TranspileWarning]]:
    imports: list[str] = []
    warnings: list[TranspileWarning] = []
    components: list[Component] = []
    current: Optional[Component] = None
    depth = 0

    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        code, comment = strip_line_comment(raw_line)
        stripped = code.strip()

        if not stripped and current is None:
            continue

        m_import = IMPORT_RE.match(stripped)
        if m_import and current is None:
            imports.append(m_import.group("path"))
            continue

        if GLOBAL_REEXPORT_RE.match(stripped) and current is None:
            continue

        m_comp = COMPONENT_RE.match(stripped)
        if m_comp and current is None:
            current = Component(
                name=normalize_identifier(m_comp.group("name")),
                base=m_comp.group("base") or "Item",
                exported=bool(m_comp.group("export")),
                source_line=lineno,
            )
            depth = 1
            continue

        if current is None:
            if stripped:
                warnings.append(TranspileWarning(lineno, "Top-level Slint construct not converted", raw_line.strip()))
            continue

        # Track body. The closing brace at depth 1 ends the component and is not
        # part of the generated QML root body.
        delta = count_open_braces(code)
        if stripped == "}" and depth == 1:
            components.append(current)
            current = None
            depth = 0
            continue

        current.body_lines.append((lineno, raw_line.rstrip()))
        depth += delta
        if depth <= 0:
            components.append(current)
            current = None
            depth = 0

    if current is not None:
        warnings.append(TranspileWarning(current.source_line, "Unclosed component; converted best effort", current.name))
        components.append(current)

    if not components and text.strip():
        # Wrap loose UI into a Main component to avoid losing work.
        comp = Component("Main", "Window", True, 1)
        comp.body_lines = list(enumerate(text.splitlines(), start=1))
        components.append(comp)
        warnings.append(TranspileWarning(1, "No component declaration found; wrapped file as Main.qml", source_name))

    return components, imports, warnings


class BodyTranspiler:
    def __init__(self) -> None:
        self.warnings: list[TranspileWarning] = []
        self.used_types: set[str] = set()
        self.indent = 1
        self.pending_for_delegate: list[tuple[int, str, Optional[str]]] = []

    def q(self, text: str = "", extra_indent: int = 0) -> str:
        return "    " * max(0, self.indent + extra_indent) + text

    def warn(self, lineno: int, message: str, source: str) -> None:
        self.warnings.append(TranspileWarning(lineno, message, source.strip()))

    def emit_object_open(self, qml_type: str, object_id: Optional[str] = None, extra: list[str] | None = None) -> list[str]:
        self.used_types.add(qml_type)
        out = [self.q(f"{qml_type} {{")]
        self.indent += 1
        if object_id:
            out.append(self.q(f"id: {normalize_identifier(object_id)}"))
        if extra:
            out.extend(self.q(x) for x in extra)
        return out

    def close_block(self) -> list[str]:
        self.indent = max(0, self.indent - 1)
        return [self.q("}")]

    def transform_binding(self, lineno: int, name: str, value: str) -> list[str]:
        prop = map_property(name)
        normalized = normalize_value(value)
        if prop in {"Layout.fillWidth", "Layout.fillHeight"}:
            # Slint stretch values are weights. In QML Layout a truthy fill flag
            # is the common equivalent; keep the numeric value as a comment.
            if normalized and normalized not in {"0", "false"}:
                return [self.q(f"{prop}: true  // from {name}: {normalized}")]
            return [self.q(f"{prop}: false")]
        return [self.q(f"{prop}: {normalized}")]

    def transform_event(self, lineno: int, event: str, body: str) -> list[str]:
        mapped = EVENT_MAP.get(event, "on" + camel_case(event)[:1].upper() + camel_case(event)[1:])
        if event in {"pointer-event", "touch-event"}:
            self.warn(lineno, f"{event} was mapped to {mapped}; pointer details need manual porting", body)
        body = body.strip()
        body = normalize_references(body)
        if body == "{":
            self.indent += 1
            return [self.q(f"{mapped}: {{", -1)]
        if body.startswith("{") and body.endswith("}"):
            return [self.q(f"{mapped}: {body}")]
        return [self.q(f"{mapped}: {body}")]

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
            m_binding = BINDING_RE.match(part)
            if m_binding:
                out.extend(self.transform_binding(lineno, m_binding.group("name"), m_binding.group("value")))
                continue
            out.append(self.q(f"// TODO(slint->qml): {normalize_references(part)}"))
            self.warn(lineno, "Inline statement needs manual conversion", part)
        return out

    def transform_inline_object(self, lineno: int, qml_type: str, body: str, object_id: Optional[str] = None) -> list[str]:
        out = self.emit_object_open(qml_type, object_id=object_id)
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
        out.append(self.q(f"property var {normalize_identifier(var)}: modelData"))
        if idx:
            out.append(self.q(f"property int {normalize_identifier(idx)}: index"))
        self.warn(lineno, "Slint for-loop converted to Repeater; check model roles and delegate sizing", f"for {var} in {model}: {typ}")
        return out

    def transform_line(self, lineno: int, raw_line: str) -> list[str]:
        code, comment = strip_line_comment(raw_line)
        stripped = code.strip()
        if not stripped:
            return [self.q(comment) if comment else ""]

        # Raw closing braces. Multiple braces on one line are uncommon in Slint UI
        # bodies; close one by one for readable QML.
        if stripped in {"}", "};", "},"}:
            return self.close_block()

        for pattern, message in UNSUPPORTED_PATTERNS:
            if pattern.match(stripped):
                self.warn(lineno, message, raw_line)
                return [self.q(f"// TODO(slint->qml): {message}: {stripped}")]

        m_for_inline = FOR_INLINE_OBJECT_RE.match(stripped)
        if m_for_inline:
            out = self.transform_for_object(
                lineno,
                m_for_inline.group("var"),
                m_for_inline.group("idx"),
                m_for_inline.group("model"),
                m_for_inline.group("type"),
            )
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
            out.extend(self.transform_inline_body(lineno, m_if_inline.group("body")))
            out.extend(self.close_block())
            return out

        m_inline = INLINE_OBJECT_RE.match(stripped)
        if m_inline:
            qml_type = map_type(m_inline.group("type"))
            return self.transform_inline_object(lineno, qml_type, m_inline.group("body"), m_inline.group("id"))

        m_prop = PROPERTY_RE.match(stripped)
        if m_prop:
            qml_type = map_slint_type(m_prop.group("type"))
            name = qml_member_identifier(m_prop.group("name"))
            value = m_prop.group("value")
            direction = m_prop.group("direction") or "in-out"
            prefix = "readonly property" if direction == "out" else "property"
            if value is not None and value.strip():
                return [self.q(f"{prefix} {qml_type} {name}: {normalize_value(value)}")]
            return [self.q(f"{prefix} {qml_type} {name}")]

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

        m_binding = BINDING_RE.match(stripped)
        if m_binding:
            return self.transform_binding(lineno, m_binding.group("name"), m_binding.group("value"))

        # Assignments and JS-like statements in handlers mostly pass through.
        if stripped.endswith(";") or stripped.startswith(("let ", "return ", "if ", "for ", "while ")):
            return [self.q(stripped)]

        self.warn(lineno, "Line copied as TODO comment; manual conversion required", raw_line)
        return [self.q(f"// TODO(slint->qml): {stripped}")]

    def transform_body(self, component: Component) -> tuple[list[str], list[TranspileWarning], set[str]]:
        out: list[str] = []
        for lineno, line in component.body_lines:
            transformed = self.transform_line(lineno, line)
            out.extend(transformed)
        # Defensive close for unbalanced bodies.
        while self.indent > 1:
            self.indent -= 1
            out.append(self.q("}"))
        return out, self.warnings, self.used_types


def build_imports(used_types: set[str]) -> list[str]:
    imports = ["import QtQuick", "import QtQuick.Controls", "import QtQuick.Layouts"]
    if any(TYPE_QML_IMPORT_HINTS.get(t) == "QtQuick.Shapes" for t in used_types):
        imports.append("import QtQuick.Shapes")
    # Keep imports stable and broad; QML ignores unused imports better than it
    # tolerates missing ones during migration.
    return imports


def qml_component_text(component: Component) -> tuple[str, list[TranspileWarning], set[str]]:
    qml_type = map_type(component.base)
    body_transpiler = BodyTranspiler()
    body_transpiler.used_types.add(qml_type)
    body_lines, warnings, used_types = body_transpiler.transform_body(component)
    imports = build_imports(used_types)

    lines: list[str] = []
    lines.extend(imports)
    lines.append("")
    lines.append(f"{qml_type} {{")
    lines.append(f"    id: root")
    if qml_type == "ApplicationWindow":
        # Slint windows are visible by default once shown from Rust/C++; QML apps
        # launched directly need this explicit binding.
        if not any(re.match(r"^    visible\s*:", line) for line in body_lines):
            lines.append("    visible: true")
    lines.extend(body_lines)
    lines.append("}")
    lines.append("")
    return "\n".join(lines), warnings, used_types


def transpile_text(text: str, source_name: str = "<memory>") -> TranspileResult:
    components, imports, warnings = extract_components(text, source_name)
    outputs: dict[str, str] = {}
    for component in components:
        qml_text, body_warnings, _used = qml_component_text(component)
        warnings.extend(body_warnings)
        outputs[f"{component.name}.qml"] = qml_text
    return TranspileResult(source=source_name, outputs=outputs, warnings=warnings, imports=imports)


def transpile_file(path: Path, out_dir: Path, *, overwrite: bool = False, main_alias: bool = True) -> TranspileResult:
    text = path.read_text(encoding="utf-8")
    result = transpile_text(text, str(path))
    out_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, str] = {}
    for name, qml in result.outputs.items():
        target = out_dir / name
        if target.exists() and not overwrite:
            stem = path.stem
            target = out_dir / f"{stem}_{name}"
        target.write_text(qml, encoding="utf-8")
        written[target.name] = qml

    # If there is exactly one component and it looks like a main window, also
    # create/update Main.qml for CMake/QML app shells.
    if main_alias and len(result.outputs) == 1:
        only_name = next(iter(result.outputs))
        component_stem = Path(only_name).stem.lower()
        if component_stem in {"main", "mainwindow", "app", "appwindow", "window"}:
            main_target = out_dir / "Main.qml"
            if overwrite or not main_target.exists():
                main_target.write_text(next(iter(result.outputs.values())), encoding="utf-8")
                written["Main.qml"] = next(iter(result.outputs.values()))

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
    parser.add_argument("-o", "--out-dir", type=Path, default=Path("qml"), help="directory for generated .qml files")
    parser.add_argument("--overwrite", action="store_true", help="overwrite existing QML files")
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
            for warning in result.warnings[:20]:
                print(f"  warning line {warning.line}: {warning.message}: {warning.source}")
            if len(result.warnings) > 20:
                print(f"  ... {len(result.warnings) - 20} more warnings")
        print(f"Warnings: {total_warnings}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
