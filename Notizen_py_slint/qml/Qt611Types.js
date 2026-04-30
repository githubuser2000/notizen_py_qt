.pragma library

// Generated helper library for migrated enum/struct declarations.
// Review usages and replace with typed C++/Rust/QML models where needed.

function makeNoteRow(values) {
    values = values || {};
    return {
        label: values.label !== undefined ? values.label : "",
        selected: values.selected !== undefined ? values.selected : false
    };
}
