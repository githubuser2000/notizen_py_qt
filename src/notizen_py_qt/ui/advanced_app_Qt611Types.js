.pragma library

// Generated helper library for migrated enum/struct declarations.
// Review usages and replace with typed C++/Rust/QML models where needed.

var Theme = Object.freeze({
    Light: 0,
    Dark: 2
});

function makeTodoItem(values) {
    values = values || {};
    return {
        title: values.title !== undefined ? values.title : "",
        done: values.done !== undefined ? values.done : false
    };
}
