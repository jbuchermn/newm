# PKGBUILD for newm

pkgname=newm
pkgver=0.1
pkgrel=1
pkgdesc="Wayland compositor"
url="https://github.com/jbuchermn/newm"
# fuzzywuzzy pyfiglet
depends=(
    'python3'
    'wayland'
    'python-cairo'
    'python-websockets'
    'python-pam'
    'python-evdev'
    'python-imageio'
    'python-numpy'
)
makedepends=('python3' 'meson' 'ninja')
license=('MIT')
arch=('any')
source=(
	'git://github.com/jbuchermn/pywm.git#branch=v0.1'
	'git://github.com/jbuchermn/newm.git#branch=v0.1'
)
md5sums=(
	'SKIP'
	'SKIP'
)
prepare() {
    cd $srcdir/pywm
    git submodule init
    git submodule update
}
build() {
    cd $srcdir/pywm
    python3 setup.py build
    cd $srcdir/newm
    python3 setup.py build
}
package() {
    cd $srcdir/pywm
    python3 setup.py install --root="$pkgdir" --optimize=1
    cd $srcdir/newm
    python3 setup.py install --root="$pkgdir" --optimize=1
}
