#[cxx_qt::bridge]
mod ffi {
    extern "RustQt" {
        #[qobject]
        #[qml_element]
        #[qproperty(QString, source)]
        #[qproperty(QString, output)]
        type TranspilerBackend = super::TranspilerBackendRust;
    }

    extern "RustQt" {
        #[qinvokable]
        fn transpile(self: Pin<&mut TranspilerBackend>);
    }
}

use core::pin::Pin;
use cxx_qt_lib::QString;

#[derive(Default)]
pub struct TranspilerBackendRust {
    source: QString,
    output: QString,
}

impl ffi::TranspilerBackend {
    pub fn transpile(self: Pin<&mut Self>) {
        let source = self.as_ref().source().to_string();
        let translated = format!("// TODO: real transpiler output\n{}", source);
        self.set_output(QString::from(translated));
    }
}
