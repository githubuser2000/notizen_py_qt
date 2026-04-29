cmake_minimum_required(VERSION 3.25)

project(NotizenQt611RustCxxQt LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(Qt6 6.11 REQUIRED COMPONENTS Core Gui Qml Quick QuickControls2)
qt_standard_project_setup(REQUIRES 6.11)

# In a full project, add the Rust crate through CXX-Qt-CMake/Corrosion.
# The Cargo template in this directory contains the CXX-Qt build.rs setup.
qt_add_executable(notizen_qt611_rust
    cpp/main.cpp
)

target_link_libraries(notizen_qt611_rust
    PRIVATE Qt6::Core Qt6::Gui Qt6::Qml Qt6::Quick Qt6::QuickControls2
)
