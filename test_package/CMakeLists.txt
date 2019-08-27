cmake_minimum_required(VERSION 2.8.12)
project(test_package)

set(CMAKE_VERBOSE_MAKEFILE TRUE)

include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()

file(COPY ${CMAKE_CURRENT_SOURCE_DIR}/en_US.dic
    DESTINATION ${CMAKE_CURRENT_BINARY_DIR}/en_US.dic)
file(COPY ${CMAKE_CURRENT_SOURCE_DIR}/en_US.aff
    DESTINATION ${CMAKE_CURRENT_BINARY_DIR}/en_US.aff)
add_executable(${PROJECT_NAME} test_package.cpp)
target_link_libraries(${PROJECT_NAME} ${CONAN_LIBS})
