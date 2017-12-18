from conans import ConanFile

class GlibTestConan(ConanFile):
    generators = 'qbs'

    def build(self):
        self.run('qbs -f "%s"' % self.source_folder)

    def imports(self):
        self.copy('*.dylib', dst='bin', src='lib')

    def test(self):
        self.run('qbs run')

        # Ensure we only link to system libraries and to libraries we built.
        self.run('! (otool -L bin/libglib.dylib | tail +3 | egrep -v "^\s*(/usr/lib/|/System/|@rpath/)")')

        # Ensure we don't search any absolute rpaths.
        self.run('! (otool -l bin/libglib.dylib | grep -A2 LC_RPATH | grep path | cut -b 15- | cut -d"(" -f1 | egrep -v "^[^/]")')
