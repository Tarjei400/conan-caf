#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import subprocess
from conans import ConanFile, CMake, tools
from conans.errors import ConanException


class CAFConan(ConanFile):
    name = 'caf'
    version = '0.15.5'
    description = 'An open source implementation of the Actor Model in C++'
    url = 'http://actor-framework.org'
    license = 'BSD-3-Clause'
    settings = 'os', 'compiler', 'build_type', 'arch'
    options = {'shared': [True, False], 'static': [True, False],
               'log_level': ['NONE', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE']}
    default_options = 'shared=False', 'static=True', 'log_level=NONE'

    def source(self):
        project_url = 'https://github.com/actor-framework/actor-framework'
        archive_path = "/archive/"
        archive_ext = ".tar.gz"
        download_url = project_url + archive_path + self.version + archive_ext
        tools.get(download_url)
        os.rename("actor-framework-" + self.version, "sources")
        
    def configure(self):
        if self.settings.compiler == 'gcc':
            if self.settings.compiler.version < 4.8:
                raise ConanException('g++ >= 4.8 is required, yours is %s' % self.settings.compiler.version)
            else:
                # This is temporary until support is in CAF for standard lib configuration
                # https://github.com/actor-framework/actor-framework/issues/597
                self.settings.compiler.libcxx = self._gcc_libcxx()
        if self.settings.compiler == 'clang' and str(self.settings.compiler.version) < '3.4':
            raise ConanException('clang >= 3.4 is required, yours is %s' % self.settings.compiler.version)
        if self.settings.compiler == 'Visual Studio' and str(self.settings.compiler.version) < '14':
            raise ConanException('Visual Studio >= 14 is required, yours is %s' % self.settings.compiler.version)
        if not (self.options.shared or self.options.static):
            raise ConanException('You must use at least one of shared=True or static=True')

    def _gcc_libcxx(self):
        if self.settings.compiler.version < 5:
            libcxx = 'libstdc++'
        else:
            process = subprocess.Popen(['g++', '--version', '-v'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            _, err = process.communicate()
            libcxx = 'libstdc++11' if 'with-default-libstdcxx-abi=new' in err else 'libstdc++'
        return libcxx

    def build(self):
        with tools.chdir("sources"):
            build_dir = "build"
            if not os.path.exists(build_dir):
                os.mkdir(build_dir)

            cmake = CMake(self)
            cmake.parallel = True
            cmake.definitions['CMAKE_CXX_STANDARD'] = '11'
            if tools.os_info.is_windows or self.settings.arch == 'x86':
                cmake.definitions['CAF_NO_OPENSSL'] = 'ON'
            for define in ['CAF_NO_EXAMPLES', 'CAF_NO_TOOLS', 'CAF_NO_UNIT_TESTS', 'CAF_NO_PYTHON']:
                cmake.definitions[define] = 'ON'
            if tools.os_info.is_macos and self.settings.arch == 'x86':
                cmake.definitions['CMAKE_OSX_ARCHITECTURES'] = 'i386'
            if self.options.static:
                static_def = 'CAF_BUILD_STATIC' if self.options.shared else 'CAF_BUILD_STATIC_ONLY'
                cmake.definitions[static_def] = 'ON'
            if self.options.log_level and self.options.log_level != 'NONE':
                cmake.definitions['CAF_LOG_LEVEL'] = self.options.log_level

            cmake.configure(source_dir="sources")
            cmake.build()

    def package(self):
        caf_include_dir = os.path.join('include','caf')
        self.copy('*.hpp',    dst=caf_include_dir,  src=os.path.join("sources", 'libcaf_core', 'caf'))
        self.copy('*.hpp',    dst=caf_include_dir,  src=os.path.join("sources", 'libcaf_io', 'caf'))
        self.copy('*.dylib',  dst='lib',                    src='lib')
        self.copy('*.so',     dst='lib',                    src='lib')
        self.copy('*.so.*',  dst='lib',                    src='lib')
        self.copy('*.a',      dst='lib',                    src='lib')
        self.copy('*.lib',    dst='lib',                    src='lib')
        self.copy('license*', dst='licenses',    ignore_case=True, keep_path=False)

    def package_info(self):
        self.cpp_info.libs = []
        if self.options.shared:
            self.cpp_info.libs.extend(['caf_io', 'caf_core'])
        if self.options.static:
            self.cpp_info.libs.extend(['caf_io_static', 'caf_core_static'])
