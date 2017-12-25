from conans import ConanFile, tools, AutoToolsBuildEnvironment
import shutil
import os

class GlibConan(ConanFile):
    name = 'glib'

    source_version = '2.51.1'
    package_version = '3'
    version = '%s-%s' % (source_version, package_version)

    requires = 'libffi/3.0.11-2@vuo/stable', \
               'gettext/0.19.8.1-2@vuo/stable'
    settings = 'os', 'compiler', 'build_type', 'arch'
    url = 'https://github.com/vuo/conan-glib'
    license = 'https://developer.gnome.org/glib/stable/glib.html'
    description = 'Core application building blocks for GNOME libraries and applications'
    source_dir = 'glib-%s' % source_version
    build_dir = '_build'

    def source(self):
        # glib is only available as .xz, but Conan's `tools.get` doesn't yet support that archive format.
        # https://github.com/conan-io/conan/issues/52
        url = 'https://download.gnome.org/sources/glib/2.51/glib-%s.tar.xz' % self.source_version
        filename = os.path.basename(url)
        tools.download(url, filename)
        tools.check_sha256(filename, '1f8e40cde43ac0bcf61defb147326d038310d75d4e50f728f6becfd2a36ac0ac')
        self.run('tar xf "%s"' % filename)
        os.unlink(filename)

    def imports(self):
        self.copy('*.dylib', self.build_dir, 'lib')

    def build(self):
        tools.mkdir(self.build_dir)
        with tools.chdir(self.build_dir):
            autotools = AutoToolsBuildEnvironment(self)
            autotools.flags.append('-Oz')
            autotools.flags.append('-mmacosx-version-min=10.10')
            autotools.link_flags.append('-Wl,-rpath,@loader_path')
            autotools.link_flags.append('-Wl,-rpath,@loader_path/../..')

            env_vars = {'PKG_CONFIG_PATH': self.deps_cpp_info["libffi"].rootpath}
            with tools.environment_append(env_vars):
                autotools.configure(configure_dir='../%s' % self.source_dir,
                                    args=['--quiet',
                                          '--without-pcre',
                                          '--disable-fam',
                                          '--prefix=%s/%s' % (self.build_folder, self.build_dir)])
                autotools.make(args=['install'])

            shutil.move('glib/.libs/libglib-2.0.0.dylib', 'glib/.libs/libglib.dylib')
            self.run('install_name_tool -id @rpath/libglib.dylib glib/.libs/libglib.dylib')
            tools.replace_in_file('glib-2.0.pc',
                                  'prefix=%s/%s' % (self.build_folder, self.build_dir),
                                  'prefix=%s' % self.package_folder)
            tools.replace_in_file('glib-2.0.pc',
                                  '-lglib-2.0',
                                  '-lglib')
 
    def package(self):
        self.copy('*.h', src='%s/include/glib-2.0' % self.build_dir, dst='include')
        self.copy('*.h', src='%s/glib' % self.build_dir, dst='include')
        self.copy('libglib.dylib', src='%s/glib/.libs' % self.build_dir, dst='lib')
        self.copy('glib-2.0.pc', src=self.build_dir, dst='', keep_path=False)

    def package_info(self):
        self.cpp_info.libs = ['glib']
