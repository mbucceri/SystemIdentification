cmake_minimum_required(VERSION 3.30)

project(
    SystemIdECMaster
    VERSION 0.1.0
    LANGUAGES CXX
)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

function(project_warnings target)
    target_compile_options(${target} PRIVATE
        -Wall
        -Wextra
        -Wpedantic
        -Werror
    )
endfunction()

add_executable(SystemIdECMaster
    src/main.cpp
)
project_warnings(SystemIdECMaster)

enable_testing()

add_executable(bootstrap-test
    tests/bootstrap_test.cpp
)
project_warnings(bootstrap-test)

add_test(
    NAME bootstrap-test
    COMMAND bootstrap-test
)