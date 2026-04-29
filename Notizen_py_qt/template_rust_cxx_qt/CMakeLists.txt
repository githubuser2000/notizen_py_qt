cmake_minimum_required(VERSION 3.25)

project(NotizenQt611RustCxxQt LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)

find_package(Qt6 6.11 REQUIRED COMPONENTS Core Gui Qml Quick QuickControls2)
qt_standard_project_setup(REQUIRES 6.11)

# This template is primarily Cargo/CXX-Qt based. For full CMake integration,
# add the Rust crate with Corrosion or CXX-Qt's CMake workflow and link the
# generated QObject library into this executable.
qt_add_executable(notizen_qt611_rust
    cpp/main.cpp
)

file(GLOB_RECURSE NOTIZEN_QML_FILES CONFIGURE_DEPENDS
    qml/*.qml
)

qt_add_qml_module(notizen_qt611_rust
    URI Notizen
    VERSION 1.0
    QML_FILES
        ${NOTIZEN_QML_FILES}
)

target_link_libraries(notizen_qt611_rust
    PRIVATE Qt6::Core Qt6::Gui Qt6::Qml Qt6::Quick Qt6::QuickControls2
)
