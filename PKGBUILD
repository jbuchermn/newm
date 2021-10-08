# PKGBUILD for newm

pkgname=newm
pkgver=0.1
pkgrel=1
pkgdesc="Wayland compositor"
url="https://github.com/jbuchermn/newm"
depends=('python3' 'wayland')
makedepends=('python3' 'meson' 'ninja')
license=('MIT')
arch=('any')
source=('git://github.com/jbuchermn/newm.git#branch=v0.1')
md5sums=('SKIP')
build() {
    cd $srcdir/newm
    python3 setup.py build
}
package() {
    cd $srcdir/newm
    python3 setup.py install --root="$pkgdir" --optimize=1
}
