cmake_minimum_required(VERSION 3.25)

project(NotizenQt611 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)

find_package(Qt6 6.11 REQUIRED COMPONENTS Core Gui Qml Quick QuickControls2)
qt_standard_project_setup(REQUIRES 6.11)

qt_add_executable(notizen_qt611
    cpp/main.cpp
)

file(GLOB_RECURSE NOTIZEN_QML_FILES CONFIGURE_DEPENDS
    qml/*.qml
)

file(GLOB_RECURSE NOTIZEN_QML_JS_FILES CONFIGURE_DEPENDS
    qml/*.js
)

include(${CMAKE_CURRENT_SOURCE_DIR}/qml/GeneratedQmlSingletons.cmake OPTIONAL)

qt_add_qml_module(notizen_qt611
    URI Notizen
    VERSION 1.0
    QML_FILES
        ${NOTIZEN_QML_FILES}
    RESOURCES
        ${NOTIZEN_QML_JS_FILES}
)

target_link_libraries(notizen_qt611
    PRIVATE
        Qt6::Core
        Qt6::Gui
        Qt6::Qml
        Qt6::Quick
        Qt6::QuickControls2
)
