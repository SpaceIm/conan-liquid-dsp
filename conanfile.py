from conans import ConanFile, AutoToolsBuildEnvironment, tools
from conans.errors import ConanInvalidConfiguration
import os

required_conan_version = ">=1.33.0"


class LiquidDspConan(ConanFile):
    name = "liquid-dsp"
    description = "Digital signal processing library for software-defined radios."
    license = "MIT"
    topics = ("dsp", "sdr", "liquid-dsp")
    homepage = "https://liquidsdr.org"
    url = "https://github.com/conan-io/conan-center-index"

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }

    @property
    def _source_subfolder(self):
        return "source_subfolder"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            del self.options.fPIC
        del self.settings.compiler.cppstd
        del self.settings.compiler.libcxx

    def validate(self):
        if self.settings.compiler == "Visual Studio":
            raise ConanInvalidConfiguration("liquid-dsp does not support Visual Studio")
        # FIXME: static on macos should work, there is something to fix in upstream makefile.in
        if tools.is_apple_os(self.settings.os) and not self.options.shared:
            raise ConanInvalidConfiguration("Issue with liquid-dsp static and libtool")

    def build_requirements(self):
        self.build_requires("libtool/2.4.6")
        if tools.os_info.is_windows and not tools.get_env("CONAN_BASH_PATH"):
            self.build_requires("msys2/cci.latest")

    def source(self):
        tools.get(**self.conan_data["sources"][self.version],
                  destination=self._source_subfolder, strip_root=True)

    def build(self):
        with tools.chdir(self._source_subfolder):
            self.run("{}".format(tools.get_env("ACLOCAL")), win_bash=tools.os_info.is_windows)
            self.run("{}".format(tools.get_env("AUTOCONF")), win_bash=tools.os_info.is_windows)
            self.run("{}".format(tools.get_env("AUTOHEADER")), win_bash=tools.os_info.is_windows)
            autotools = AutoToolsBuildEnvironment(self, win_bash=tools.os_info.is_windows)
            autotools.configure()
            if tools.is_apple_os(self.settings.os):
                target = "libliquid.dylib" if self.options.shared else "libliquid.ar"
            elif self.settings.os == "Windows":
                target = "libliquid.a" # Does it work? What about shared?
            else:
                target = "libliquid.so" if self.options.shared else "libliquid.a"
            autotools.make(target=target)

    def package(self):
        self.copy("LICENSE", dst="licenses", src=self._source_subfolder)
        self.copy("config.h", dst=os.path.join("include", "liquid"), src=self._source_subfolder)
        self.copy("*.h", dst=os.path.join("include", "liquid"), src=os.path.join(self._source_subfolder, "include"))
        self.copy("*.a", dst="lib", src=self._source_subfolder, keep_path=False)
        self.copy("*.so*", dst="lib", src=self._source_subfolder, keep_path=False)
        self.copy("*.dylib", dst="lib", src=self._source_subfolder, keep_path=False)

    def package_info(self):
        self.cpp_info.libs = ["liquid"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.append("m")
