#!/bin/bash

# Ensure script is run as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run this installer as root (e.g. using sudo)"
  exit 1
fi

echo "Installing dependencies..."
# Check for apt and install python dependencies
if command -v apt-get &> /dev/null; then
    apt-get update
    apt-get install -y python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 python3-dnslib python3-pystray python3-pil
else
    echo "Warning: apt-get not found. Assuming dependencies are already installed or will be installed via your package manager."
fi

echo "Setting up application files in /opt/dns66-client..."
mkdir -p /opt/dns66-client
mkdir -p /opt/dns66-client/cache
cp -r icons /opt/dns66-client/ || true
cp dns_proxy.py /opt/dns66-client/
cp ui.py /opt/dns66-client/
cp tray.py /opt/dns66-client/
cp config.json /opt/dns66-client/
cp dns66-icon.svg /usr/share/pixmaps/dns66-client.svg
cp dns66-icon.png /opt/dns66-client/
chmod +x /opt/dns66-client/dns_proxy.py
chmod +x /opt/dns66-client/ui.py
chmod +x /opt/dns66-client/tray.py
chown -R root:root /opt/dns66-client
chmod 666 /opt/dns66-client/config.json
chmod 755 /opt/dns66-client/cache

echo "Setting up systemd service..."
cp dns66-client.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable dns66-client
systemctl restart dns66-client

echo "Creating desktop shortcut..."
cat <<EOF > /usr/share/applications/dns66-client.desktop
[Desktop Entry]
Version=1.0
Name=DNS66 Client for Linux
Comment=DNS-Based Host Blocking
Exec=/usr/bin/python3 /opt/dns66-client/ui.py
Icon=dns66-client
Terminal=false
Type=Application
Categories=Network;Security;
EOF

echo "Setting up tray autostart..."
mkdir -p /etc/xdg/autostart
cp dns66-client-tray.desktop /etc/xdg/autostart/

echo "Setting up system DNS..."
# Update systemd-resolved config if it exists
if [ -d /etc/systemd/resolved.conf.d ]; then
    cat <<EOF > /etc/systemd/resolved.conf.d/dns66-client.conf
[Resolve]
DNS=127.0.0.1 ::1
Domains=~.
EOF
    systemctl restart systemd-resolved
else
    # Fallback to direct resolv.conf
    # Back up original resolv.conf if we haven't already
    if [ ! -f /etc/resolv.conf.dns66-client.bak ]; then
        cp -a /etc/resolv.conf /etc/resolv.conf.dns66-client.bak
    fi
    echo "nameserver 127.0.0.1" > /etc/resolv.conf
    echo "nameserver ::1" >> /etc/resolv.conf
fi

echo "Installation complete!"
echo "You can launch the DNS66 UI from your application menu."
