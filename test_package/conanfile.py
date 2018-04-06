from conans import ConanFile
import platform

class GlibTestConan(ConanFile):
    requires = 'llvm/3.3-5@vuo/stable'
    generators = 'qbs'

    def build(self):
        self.run('qbs -f "%s"' % self.source_folder)

    def imports(self):
        self.copy('*', src='bin', dst='bin')
        self.copy('*', src='lib', dst='lib')

    def test(self):
        self.run('qbs run -f "%s"' % self.source_folder)

        if platform.system() == 'Darwin':
            self.run('! (otool -L lib/libglib.dylib | tail +3 | egrep -v "^\s*(/usr/lib/|/System/|@rpath/)")')
            self.run('! (otool -L lib/libglib.dylib | fgrep "libstdc++")')
            self.run('! (otool -l lib/libglib.dylib | grep -A2 LC_RPATH | cut -d"(" -f1 | grep "\s*path" | egrep -v "^\s*path @(executable|loader)_path")')
        elif platform.system() == 'Linux':
            self.run('! (ldd lib/libglib.so | grep -v "^lib/" | grep "/" | egrep -v "(\s(/lib64/|(/usr)?/lib/x86_64-linux-gnu/)|test_package/build)")')
            self.run('! (ldd lib/libglib.so | fgrep "libstdc++")')
        else:
            raise Exception('Unknown platform "%s"' % platform.system())
