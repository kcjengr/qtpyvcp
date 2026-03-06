cmake_minimum_required(VERSION 3.18)
project(qtpyvcp_backplot_cpp LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

find_package(Python3 COMPONENTS Interpreter Development.Module REQUIRED)
find_package(pybind11 CONFIG QUIET)

if(NOT pybind11_FOUND)
    execute_process(
        COMMAND ${Python3_EXECUTABLE} -m pybind11 --cmakedir
        OUTPUT_VARIABLE PYBIND11_CMAKE_DIR
        OUTPUT_STRIP_TRAILING_WHITESPACE
        RESULT_VARIABLE PYBIND11_CMAKEDIR_RESULT
    )

    if(PYBIND11_CMAKEDIR_RESULT EQUAL 0 AND EXISTS "${PYBIND11_CMAKE_DIR}")
        list(APPEND CMAKE_PREFIX_PATH "${PYBIND11_CMAKE_DIR}")
        find_package(pybind11 CONFIG REQUIRED)
    else()
        message(FATAL_ERROR "pybind11 not found. Install it from Debian package manager 'sudo apt install python3-pybind11'.")
    endif()
endif()

pybind11_add_module(_backplot_cpp
    backplot_bridge_pybind.cpp
    backplot_builder.cpp
)

target_include_directories(_backplot_cpp PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})
