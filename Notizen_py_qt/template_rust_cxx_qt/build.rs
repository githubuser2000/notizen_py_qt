use cxx_qt_build::{CxxQtBuilder, QmlModule};

fn main() {
    CxxQtBuilder::new_qml_module(
        QmlModule::new("org.notizen.transpiler")
            .qml_files(["qml/Main.qml"]),
    )
    .files(["src/backend.rs"])
    .qt_module("Quick")
    .qt_module("QuickControls2")
    .build();
}
