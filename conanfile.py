from conans import ConanFile, tools, AutoToolsBuildEnvironment
import shutil
import os
import platform

class GlibConan(ConanFile):
    name = 'glib'

    source_version = '2.51.1'
    package_version = '4'
    version = '%s-%s' % (source_version, package_version)

    build_requires = 'llvm/3.3-5@vuo/stable'
    requires = 'libffi/3.0.12-3@vuo/stable', \
               'gettext/0.19.8.1-3@vuo/stable'
    settings = 'os', 'compiler', 'build_type', 'arch'
    url = 'https://github.com/vuo/conan-glib'
    license = 'https://developer.gnome.org/glib/stable/glib.html'
    description = 'Core application building blocks for GNOME libraries and applications'
    source_dir = 'glib-%s' % source_version
    build_dir = '_build'
    exports_sources = '*.patch'

    def requirements(self):
        if platform.system() == 'Linux':
            self.requires('patchelf/0.10pre-1@vuo/stable')
        elif platform.system() != 'Darwin':
            raise Exception('Unknown platform "%s"' % platform.system())

    def source(self):
        # glib is only available as .xz, but Conan's `tools.get` doesn't yet support that archive format.
        # https://github.com/conan-io/conan/issues/52
        url = 'https://download.gnome.org/sources/glib/2.51/glib-%s.tar.xz' % self.source_version
        filename = os.path.basename(url)
        tools.download(url, filename)
        tools.check_sha256(filename, '1f8e40cde43ac0bcf61defb147326d038310d75d4e50f728f6becfd2a36ac0ac')
        self.run('tar xf "%s"' % filename)
        os.unlink(filename)

        tools.patch(patch_file='cocoa-compatibility.patch', base_path=self.source_dir)

        self.run('mv %s/COPYING %s/%s.txt' % (self.source_dir, self.source_dir, self.name))

    def imports(self):
        self.copy('*', self.build_dir, 'lib')

    def build(self):
        tools.mkdir(self.build_dir)
        with tools.chdir(self.build_dir):
            autotools = AutoToolsBuildEnvironment(self)

            # The LLVM/Clang libs get automatically added by the `requires` line,
            # but this package doesn't need to link with them.
            autotools.libs = ['c++abi']

            autotools.flags.append('-Oz')

            if platform.system() == 'Darwin':
                autotools.flags.append('-mmacosx-version-min=10.10')
                autotools.flags.append('-isysroot /Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX10.10.sdk')
                autotools.link_flags.append('-Wl,-rpath,@loader_path')
                autotools.link_flags.append('-Wl,-rpath,@loader_path/../..')

            env_vars = {
                'CC' : self.deps_cpp_info['llvm'].rootpath + '/bin/clang',
                'CXX': self.deps_cpp_info['llvm'].rootpath + '/bin/clang++',
                'PKG_CONFIG_PATH': self.deps_cpp_info["libffi"].rootpath,
            }
            with tools.environment_append(env_vars):
                autotools.configure(configure_dir='../%s' % self.source_dir,
                                    args=['--quiet',
                                          '--without-pcre',
                                          '--disable-fam',
                                          '--prefix=%s/%s' % (self.build_folder, self.build_dir)])
                autotools.make(args=['install'])

            if platform.system() == 'Darwin':
                shutil.move('glib/.libs/libglib-2.0.0.dylib', 'glib/.libs/libglib.dylib')
                self.run('install_name_tool -id @rpath/libglib.dylib glib/.libs/libglib.dylib')
            elif platform.system() == 'Linux':
                shutil.move('lib/libglib-2.0.so.0.5101.0', 'lib/libglib.so')
                patchelf = self.deps_cpp_info['patchelf'].rootpath + '/bin/patchelf'
                self.run('%s --set-soname libglib.so lib/libglib.so' % patchelf)

            tools.replace_in_file('glib-2.0.pc',
                                  'prefix=%s/%s' % (self.build_folder, self.build_dir),
                                  'prefix=%s' % self.package_folder)
            tools.replace_in_file('glib-2.0.pc',
                                  '-lglib-2.0',
                                  '-lglib')
 
    def package(self):
        if platform.system() == 'Darwin':
            libext = 'dylib'
        elif platform.system() == 'Linux':
            libext = 'so'
        else:
            raise Exception('Unknown platform "%s"' % platform.system())

        self.copy('*.h', src='%s/include/glib-2.0' % self.build_dir, dst='include')
        self.copy('*.h', src='%s/glib' % self.build_dir, dst='include')
        self.copy('libglib.%s' % libext, src='%s/glib/.libs' % self.build_dir, dst='lib')
        self.copy('libglib.%s' % libext, src='%s/lib' % self.build_dir, dst='lib')
        self.copy('glib-2.0.pc', src=self.build_dir, dst='', keep_path=False)

        self.copy('%s.txt' % self.name, src=self.source_dir, dst='license')

    def package_info(self):
        self.cpp_info.libs = ['glib']
