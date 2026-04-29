#[cxx_qt::bridge]
pub mod qobject {
    unsafe extern "C++" {
        include!("cxx-qt-lib/qstring.h");
        type QString = cxx_qt_lib::QString;
    }

    extern "RustQt" {
        #[qobject]
        #[qml_element]
        #[qproperty(QString, source)]
        #[qproperty(QString, output)]
        type TranspilerBackend = super::TranspilerBackendRust;

        #[qinvokable]
        fn transpile(self: Pin<&mut Self>);
    }
}

use core::pin::Pin;
use cxx_qt_lib::QString;

#[derive(Default)]
pub struct TranspilerBackendRust {
    source: QString,
    output: QString,
}

impl qobject::TranspilerBackend {
    pub fn transpile(self: Pin<&mut Self>) {
        let source = self.as_ref().source().to_string();
        let translated = format!("// TODO: plug real transpiler core here\n{}", source);
        self.set_output(QString::from(translated));
    }
}
