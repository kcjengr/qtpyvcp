cmake_minimum_required(VERSION 3.18)
project(qtpyvcp_gcodeeditor_plugin LANGUAGES CXX)

set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTOUIC ON)
set(CMAKE_AUTORCC ON)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

find_package(Qt6 REQUIRED COMPONENTS Core Gui Widgets Designer)

add_library(gcodeeditorplugin MODULE
    gcodeeditor.cpp
    gcodeeditor.h
    gcodehighlighter.cpp
    gcodehighlighter.h
    gcodeeditorplugin.cpp
    gcodeeditorplugin.h
)

target_link_libraries(gcodeeditorplugin PRIVATE
    Qt6::Core
    Qt6::Gui
    Qt6::Widgets
    Qt6::Designer
)

# Remove 'lib' prefix so output matches Qt Designer plugin naming conventions.
set_target_properties(gcodeeditorplugin PROPERTIES PREFIX "")
