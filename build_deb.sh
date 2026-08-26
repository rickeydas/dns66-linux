#!/bin/bash
set -e

# Remove old packages and build directories
rm -f dns66-client_*.deb
rm -rf dns66-client_*_all

TIMESTAMP=$(date +"%Y%m%d%H%M%S")
DIR="dns66-client_1.0-${TIMESTAMP}_all"
mkdir -p "$DIR/DEBIAN"
mkdir -p "$DIR/opt/dns66-client"
mkdir -p "$DIR/usr/share/applications"

# Control file
cat << EOF > "$DIR/DEBIAN/control"
Package: dns66-client
Version: 1.0-${TIMESTAMP}
Section: base
Priority: optional
Architecture: all
Depends: python3, python3-gi, gir1.2-gtk-4.0, gir1.2-adw-1, pkexec
Maintainer: Developer
Description: System-wide DNS Proxy and Adblocker
 A Linux port of the DNS66 adblocker that operates locally.
EOF

# postinst script
cat << 'POST' > "$DIR/DEBIAN/postinst"
#!/bin/bash
set -e
chmod +x /opt/dns66-client/install.sh
chmod +x /opt/dns66-client/uninstall.sh
/opt/dns66-client/install.sh
POST
chmod +x "$DIR/DEBIAN/postinst"

# prerm script
cat << 'PRERM' > "$DIR/DEBIAN/prerm"
#!/bin/bash
set -e
if [ -f /opt/dns66-client/uninstall.sh ]; then
    /opt/dns66-client/uninstall.sh
fi
PRERM
chmod +x "$DIR/DEBIAN/prerm"

# Copy application files
cp -r icons "$DIR/opt/dns66-client/" || true
cp *.py *.json *.sh *.service *.svg *.png "$DIR/opt/dns66-client/" || true
cp dns66-client.desktop "$DIR/usr/share/applications/" || true

dpkg-deb --build "$DIR"
echo "Package built: ${DIR}.deb"

# Clean up build directory after packaging
rm -rf "$DIR"
