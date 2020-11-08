from conans import ConanFile, tools, Meson
import shutil
import os
import platform

class GlibConan(ConanFile):
    name = 'glib'

    source_version = '2.66.2'
    package_version = '0'
    version = '%s-%s' % (source_version, package_version)

    build_requires = (
        'llvm/5.0.2-1@vuo/stable',
        'macos-sdk/11.0-0@vuo/stable',
    )
    requires = (
        'libffi/3.4pre-0@vuo/stable',
        'gettext/0.21-0@vuo/stable',
    )
    settings = 'os', 'compiler', 'build_type', 'arch'
    url = 'https://github.com/vuo/conan-glib'
    license = 'https://developer.gnome.org/glib/stable/glib.html'
    description = 'Core application building blocks for GNOME libraries and applications'
    source_dir = 'glib-%s' % source_version
    generators = 'pkg_config'

    build_x86_dir = '_build_x86'
    build_arm_dir = '_build_arm'
    install_x86_dir = '_install_x86'
    install_arm_dir = '_install_arm'
    install_universal_dir = '_install_universal_dir'

    exports_sources = '*.patch'

    def requirements(self):
        if platform.system() == 'Linux':
            self.requires('patchelf/0.10pre-1@vuo/stable')
        elif platform.system() != 'Darwin':
            raise Exception('Unknown platform "%s"' % platform.system())

    def source(self):
        tools.get('https://download.gnome.org/sources/glib/2.66/glib-%s.tar.xz' % self.source_version,
                  sha256='ec390bed4e8dd0f89e918f385e8d4cfd7470b1ef7c1ce93ec5c4fc6e3c6a17c4')

        self.run('mv %s/COPYING %s/%s.txt' % (self.source_dir, self.source_dir, self.name))

    def imports(self):
        self.copy('*', self.build_x86_dir, 'lib')
        self.copy('*', self.build_arm_dir, 'lib')

    def build(self):
        defs = {
            'nls'          : 'disabled',
            'glib_assert'  : 'false',
            'glib_checks'  : 'false',
            'xattr'        : 'false',
            'libmount'     : 'disabled',
            'selinux'      : 'disabled',
            'internal_pcre': 'true',
        }

        flags  = '-isysroot %s' % self.deps_cpp_info['macos-sdk'].rootpath
        flags += ' -mmacosx-version-min=10.11'


        self.output.info("=== Build for x86_64 ===")
        with tools.environment_append({
            'CC'      : self.deps_cpp_info['llvm'].rootpath + '/bin/clang',
            'CXX'     : self.deps_cpp_info['llvm'].rootpath + '/bin/clang++',
            'CFLAGS'  : flags,
            'CPPFLAGS': flags,
            'LDFLAGS' : flags,
        }):
            meson = Meson(self)
            defs_x86 = defs.copy()
            defs_x86['prefix'] = '%s/%s' % (os.getcwd(), self.install_x86_dir)
            meson.configure(
                source_folder=self.source_dir,
                build_folder=self.build_x86_dir,
                defs=defs_x86)
            meson.build()
            meson.meson_install()


        self.output.info("=== Build for arm64 ===")
        flags += ' -arch arm64 -target arm64-apple-macos10.11.0'
        with tools.environment_append({
            'CC'      : self.deps_cpp_info['llvm'].rootpath + '/bin/clang',
            'CXX'     : self.deps_cpp_info['llvm'].rootpath + '/bin/clang++',
            'CFLAGS'  : flags,
            'CPPFLAGS': flags,
            'LDFLAGS' : flags,
        }):
            with open('arm64.txt', 'w') as fd:
                fd.write("""
                    [binaries]
                    c = 'clang'
                    cpp = 'clang++'
                    objc = 'clang'
                    ar = 'ar'
                    ld = 'clang++'
                    pkgconfig = 'pkg-config'
                    strip = 'strip'

                    [host_machine]
                    system = 'darwin'
                    cpu_family = 'arm'
                    cpu = 'arm64'
                    endian = 'little'
                """)
            meson = Meson(self)
            defs_arm = defs.copy()
            defs_arm['prefix'] = '%s/%s' % (os.getcwd(), self.install_arm_dir)
            meson.configure(
                source_folder=self.source_dir,
                build_folder=self.build_arm_dir,
                args=[
                    '--cross-file=arm64.txt',
                ],
                defs=defs_arm)
            meson.build()
            meson.meson_install()

 
    def package(self):
        if platform.system() == 'Darwin':
            libext = 'dylib'
        elif platform.system() == 'Linux':
            libext = 'so'
        else:
            raise Exception('Unknown platform "%s"' % platform.system())

        self.run('install_name_tool -id @rpath/libglib.dylib %s/lib/libglib-2.0.0.dylib' % self.install_x86_dir)
        self.run('install_name_tool -id @rpath/libglib.dylib %s/lib/libglib-2.0.0.dylib' % self.install_arm_dir)
        tools.mkdir(self.install_universal_dir)
        with tools.chdir(self.install_universal_dir):
            self.run('lipo -create ../%s/lib/libglib-2.0.0.%s ../%s/lib/libglib-2.0.0.%s -output libglib.%s' % (self.install_x86_dir, libext, self.install_arm_dir, libext, libext))

        self.copy('*.h', src='%s/lib/glib-2.0/include' % self.install_x86_dir, dst='include')
        self.copy('*.h', src='%s/include/glib-2.0' % self.install_x86_dir, dst='include')
        self.copy('libglib.%s' % libext, src=self.install_universal_dir, dst='lib')

        self.copy('%s.txt' % self.name, src=self.source_dir, dst='license')

    def package_info(self):
        self.cpp_info.libs = ['glib']
