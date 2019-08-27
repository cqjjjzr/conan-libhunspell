#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conans import ConanFile, tools, AutoToolsBuildEnvironment
from conans.errors import ConanInvalidConfiguration
import os
import glob


class LibhunspellConan(ConanFile):
    name = "libhunspell"
    version = "1.7.0"
    file_id = 2573619 # from https://github.com/hunspell/hunspell/files/2573619/hunspell-1.7.0.tar.gz
    description = "The most popular spellchecking library."
    url = "https://github.com/bincrafters/conan-libiconv"
    homepage = "https://github.com/hunspell/hunspell"
    author = "Charlie Jiang <cqjjjzr@126.com>"
    topics = "natural-language-processing", "spellcheck", "spellchecker", "stemming", "spell-check", "spell-checking-engine", "spell-checker"
    license = "GPL-2"
    exports = ["LICENSE.md"]
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = {'shared': False, 'fPIC': True}
    short_paths = True
    _source_subfolder = "source_subfolder"

    @property
    def _is_mingw_windows(self):
        return self.settings.os == 'Windows' and self.settings.compiler == 'gcc' and os.name == 'nt'

    @property
    def _is_msvc(self):
        return self.settings.compiler == 'Visual Studio'

    def system_requirements(self):
        try:
            installer = conans.tools.SystemPackageTool()
            installer.update()
            installer.install('autoconf')
            installer.install('automake')
            installer.install('libtool')
            installer.install('make')
            installer.install('pkg-config')
        except:
            self.output.warn('Unable to bootstrap required build tools.  If they are already installed, you can ignore this warning.')

    def build_requirements(self):
        if tools.os_info.is_windows:
            if "CONAN_BASH_PATH" not in os.environ:
                self.build_requires("msys2_installer/latest@bincrafters/stable")

    def configure(self):
        del self.settings.compiler.libcxx

    def config_options(self):
        if self.settings.os == 'Windows':
            del self.options.fPIC

    def source(self):
        archive_name = "hunspell-{0}".format(self.version)
        source_url = "https://github.com/hunspell/hunspell/files/"
        tools.get("{0}/{1}/{2}.tar.gz".format(source_url, self.file_id, archive_name),
                  sha256="57be4e03ae9dd62c3471f667a0d81a14513e314d4d92081292b90435944ff951")
        os.rename(archive_name, self._source_subfolder)

        with open(os.path.join(self._source_subfolder, "src", "Makefile.am"), "w") as f:
            f.write("SUBDIRS=hunspell\n\n")

    def _build_autotools(self):
        prefix = os.path.abspath(self.package_folder)
        rc = None
        host = None
        build = None
        if self._is_mingw_windows or self._is_msvc:
            prefix = prefix.replace('\\', '/')
            build = False
            if self.settings.arch == "x86":
                host = "i686-w64-mingw32"
                rc = "windres --target=pe-i386"
            elif self.settings.arch == "x86_64":
                host = "x86_64-w64-mingw32"
                rc = "windres --target=pe-x86-64"

        #
        # If you pass --build when building for iPhoneSimulator, the configure script halts.
        # So, disable passing --build by setting it to False.
        #
        if self.settings.os == "iOS" and self.settings.arch == "x86_64":
            build = False

        env_build = AutoToolsBuildEnvironment(self, win_bash=tools.os_info.is_windows)

        if self.settings.os != "Windows":
            env_build.fpic = self.options.fPIC

        configure_args = ['--prefix=%s' % prefix]
        if self.options.shared:
            configure_args.extend(['--disable-static', '--enable-shared'])
        else:
            configure_args.extend(['--enable-static', '--disable-shared'])

        env_vars = {}

        if rc:
            configure_args.extend(['RC=%s' % rc, 'WINDRES=%s' % rc])

        with tools.chdir(self._source_subfolder):
            with tools.environment_append(env_vars):
                self.run("autoreconf -vfi", win_bash=tools.os_info.is_windows)
                env_build.configure(args=configure_args, host=host, build=build)
                env_build.make()
                env_build.install()

    def build(self):
        with tools.vcvars(self.settings) if self._is_msvc else tools.no_op():
            self._build_autotools()

    def package(self):
        self.copy(os.path.join(self._source_subfolder, "COPYING.LIB"),
                  dst="licenses", ignore_case=True, keep_path=False)
        # remove libtool .la files - they have hard-coded paths
        with tools.chdir(os.path.join(self.package_folder, "lib")):
            for filename in glob.glob("*.la"):
                os.unlink(filename)

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
