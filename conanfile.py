#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conans import ConanFile, tools, AutoToolsBuildEnvironment, MSBuild
from conans.errors import ConanInvalidConfiguration
from conans.tools import os_info, SystemPackageTool
import os
import glob
import traceback


class LibhunspellConan(ConanFile):
    name = "libhunspell"
    version = "1.7.0"
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
            if (self._is_msvc):
                return
            if (os_info.detect_windows_subsystem() != None and os_info.detect_windows_subsystem() != 'WSL'):
                os.environ["CONAN_SYSREQUIRES_SUDO"] = "False"
            installer = SystemPackageTool()
            #installer.update()
            installer.install('autoconf')
            installer.install('automake')
            installer.install('libtool')
            installer.install('make')
            installer.install('pkg-config')
        except:
            self.output.warn('Unable to bootstrap required build tools.  If they are already installed, you can ignore this warning.')
            self.output.warn(traceback.print_exc())

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
        source_url = "https://github.com/hunspell/hunspell/archive"
        tools.get("{0}/v{1}.tar.gz".format(source_url, self.version),
                  sha256="bb27b86eb910a8285407cf3ca33b62643a02798cf2eef468c0a74f6c3ee6bc8a")
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

    def _build_msbuild(self):
        msbuild = MSBuild(self)
        with tools.chdir(self._source_subfolder):
            tools.replace_in_file("msvc\\libhunspell.vcxproj", "v140_xp", "v140")

            env_vars = tools.vcvars_dict(self.settings)
            winsdkver = env_vars["WindowsSDKVersion"].replace("\\", "")
            self.output.info('Using Windows SDK Version %s' % winsdkver)
            tools.replace_in_file("msvc\\libhunspell.vcxproj",
             "<WindowsTargetPlatformVersion>8.1</WindowsTargetPlatformVersion>", 
             "<WindowsTargetPlatformVersion>%s</WindowsTargetPlatformVersion>" % winsdkver)
            if (self.options.shared):
                msbuild.build("msvc\\libhunspell.vcxproj")
            else:
                msbuild.build("msvc\\libhunspell.vcxproj", definitions={"HUNSPELL_STATIC": None})

    def build(self):
        if self._is_msvc:
            self._build_msbuild()
        else:
            self._build_autotools()

    def package(self):
        self.copy(os.path.join(self._source_subfolder, "COPYING.LIB"),
                  dst="licenses", ignore_case=True, keep_path=False)
        # remove libtool .la files - they have hard-coded paths
        if self._is_msvc:
            include_folder = os.path.join(self._source_subfolder, "src")
            self.copy(pattern="*.hxx", dst="include", src=include_folder)
            self.copy(pattern="*.h", dst="include", src=include_folder)
            self.copy(pattern="*.dll", dst="bin", keep_path=False)
            self.copy(pattern="*.lib", dst="lib", keep_path=False)
            self.copy(pattern="*.a", dst="lib", keep_path=False)
            self.copy(pattern="*.so*", dst="lib", keep_path=False)
            self.copy(pattern="*.dylib", dst="lib", keep_path=False)
        else:
            with tools.chdir(os.path.join(self.package_folder, "lib")):
                for filename in glob.glob("*.la"):
                    os.unlink(filename)

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
        if (not self.options.shared):
            self.cpp_info.defines = ["HUNSPELL_STATIC"]
