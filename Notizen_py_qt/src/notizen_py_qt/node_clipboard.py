from __future__ import annotations

from xml.etree import ElementTree as ET

from .models import DesktopNoteState, NoteNode

NODE_MIME_TYPE = "application/x-notizen-pyqt-node+xml"
_NOTE_KNOWN_ATTRS = {
    "name",
    "title",
    "isexpanded",
    "bgcolor",
    "fgcolor",
    "visible",
    "x",
    "y",
    "width",
    "height",
    "opacity",
    "argb",
}
_DESKTOP_ATTRS = {"visible", "x", "y", "width", "height", "opacity", "argb"}


def _bool_attr(value: str | None, default: bool = True) -> bool:
    if value is None or value == "":
        return default
    return value.strip().lower() in {"true", "1", "yes", "ja"}


def _int_attr(element: ET.Element, name: str, default: int = 0) -> int:
    value = element.get(name)
    if value is None or value == "":
        return default
    try:
        return int(float(value))
    except ValueError:
        return default


def _float_attr(element: ET.Element, name: str, default: float = 0.85) -> float:
    value = element.get(name)
    if value is None or value == "":
        return default
    try:
        return float(value.replace(",", "."))
    except ValueError:
        return default


def _desktop_state_from_element(element: ET.Element) -> DesktopNoteState | None:
    if element.get("x") in (None, ""):
        return None
    return DesktopNoteState(
        x=_int_attr(element, "x", 80),
        y=_int_attr(element, "y", 80),
        width=_int_attr(element, "width", 260),
        height=_int_attr(element, "height", 220),
        visible=_bool_attr(element.get("visible"), True),
        opacity=_float_attr(element, "opacity", 0.85),
        argb=_int_attr(element, "argb", 0) if element.get("argb") not in (None, "") else None,
        legacy_sparse=True,
        legacy_attr_names={key for key in _DESKTOP_ATTRS if element.get(key) not in (None, "")},
    )


def _node_from_element(element: ET.Element, *, include_desktop_note: bool = False) -> NoteNode:
    if element.tag != "Notiz":
        raise ValueError(f"Expected Notiz element, got {element.tag!r}")
    node = NoteNode(
        title=element.get("name") or element.get("title") or "...",
        rtf=element.text or "",
        expanded=_bool_attr(element.get("isexpanded"), True),
        bg_argb=_int_attr(element, "bgcolor", 0),
        fg_argb=_int_attr(element, "fgcolor", 0),
        desktop_note=_desktop_state_from_element(element) if include_desktop_note else None,
        extra_attrs={key: value for key, value in element.attrib.items() if key not in _NOTE_KNOWN_ATTRS},
    )
    for child in element:
        if child.tag == "Notiz":
            node.add_child(_node_from_element(child, include_desktop_note=include_desktop_note))
    return node


def _element_from_node(node: NoteNode, *, include_desktop_note: bool = False) -> ET.Element:
    element = ET.Element("Notiz", dict(node.extra_attrs))
    element.set("name", node.title)
    element.set("isexpanded", "True" if node.expanded else "False")
    element.set("bgcolor", str(node.bg_argb))
    element.set("fgcolor", str(node.fg_argb))
    if include_desktop_note and node.desktop_note is not None:
        desk = node.desktop_note
        element.set("visible", "True" if desk.visible else "False")
        element.set("x", str(desk.x))
        element.set("y", str(desk.y))
        element.set("width", str(desk.width))
        element.set("height", str(desk.height))
        if (not desk.legacy_sparse) or "opacity" in desk.legacy_attr_names or desk.opacity != 0.85:
            element.set("opacity", str(desk.opacity))
        if desk.argb is not None:
            element.set("argb", str(desk.argb))
    element.text = node.rtf or ""
    for child in node.children:
        element.append(_element_from_node(child, include_desktop_note=include_desktop_note))
    return element


def node_to_clipboard_xml(node: NoteNode, *, include_desktop_note: bool = False) -> str:
    """Serialize a subtree for the Qt/system clipboard.

    The payload mirrors the legacy ALX ``Notiz`` element and adds a small wrapper
    so another running Notizen-Python/Qt instance can distinguish a copied
    subtree from arbitrary XML. Desktop-note geometry is intentionally dropped by
    default; copied notes should not reopen as duplicate floating windows.
    """
    root = ET.Element("notizen-node")
    root.append(_element_from_node(node, include_desktop_note=include_desktop_note))
    return ET.tostring(root, encoding="unicode", short_empty_elements=True)


def node_from_clipboard_xml(xml_text: str, *, include_desktop_note: bool = False) -> NoteNode:
    """Load one copied subtree from clipboard XML or a standalone Notiz element."""
    try:
        root = ET.fromstring(xml_text.strip())
    except ET.ParseError as exc:
        raise ValueError("Clipboard does not contain a Notizen subtree.") from exc

    if root.tag == "Notiz":
        element = root
    elif root.tag in {"notizen-node", "notizen-alx2"}:
        element = next((child for child in root if child.tag == "Notiz"), None)
        if element is None:
            raise ValueError("Clipboard XML contains no Notiz element.")
    else:
        raise ValueError(f"Unsupported Notizen clipboard root: {root.tag!r}")
    return _node_from_element(element, include_desktop_note=include_desktop_note)


def looks_like_node_clipboard_xml(text: str) -> bool:
    stripped = text.lstrip()
    return stripped.startswith("<notizen-node") or stripped.startswith("<Notiz") or stripped.startswith("<notizen-alx2")
