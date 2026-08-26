#!/bin/bash

if [ "$EUID" -ne 0 ]; then
  echo "Please run this uninstaller as root (e.g. using sudo)"
  exit 1
fi

echo "Stopping and disabling systemd service..."
systemctl stop dns66-client 2>/dev/null
systemctl disable dns66-client 2>/dev/null
rm -f /etc/systemd/system/dns66-client.service
systemctl daemon-reload

echo "Stopping user-session background processes..."
pkill -f "python3 /opt/dns66-client/tray.py" 2>/dev/null || true
pkill -f "python3 /opt/dns66-client/ui.py" 2>/dev/null || true

echo "Reverting system DNS settings..."
if [ -f /etc/systemd/resolved.conf.d/dns66-client.conf ]; then
    rm -f /etc/systemd/resolved.conf.d/dns66-client.conf
    systemctl restart systemd-resolved
fi

if [ -f /etc/resolv.conf.dns66-client.bak ]; then
    mv /etc/resolv.conf.dns66-client.bak /etc/resolv.conf
    echo "Restored original /etc/resolv.conf"
fi

echo "Removing application files..."
rm -rf /opt/dns66-client
rm -f /usr/share/applications/dns66-client.desktop
rm -f /etc/xdg/autostart/dns66-client-tray.desktop
rm -f /usr/share/pixmaps/dns66-client.svg

echo "Uninstallation complete. Your system has been restored to its previous state."
