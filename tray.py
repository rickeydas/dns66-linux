#!/usr/bin/env python3
import pystray
from PIL import Image, ImageDraw
import json
import os
import subprocess
import threading
import time

CONFIG_FILE = "/opt/dns66-client/config.json"

def create_image(color):
    # Generate a 64x64 colored circle icon
    image = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    dc = ImageDraw.Draw(image)
    dc.ellipse((4, 4, 60, 60), fill=color)
    return image

def get_status():
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                return config.get("service_enabled", True)
    except Exception:
        pass
    return True

def on_open_settings(icon, item):
    subprocess.Popen(["pkexec", "python3", "/opt/dns66-client/ui.py"])

def on_toggle(icon, item):
    subprocess.Popen(["pkexec", "python3", "/opt/dns66-client/ui.py", "--toggle"])
    # We will poll and update the icon shortly

def on_stop_and_quit(icon, item):
    # Stop the actual systemd background service
    subprocess.Popen(["pkexec", "systemctl", "stop", "dns66-client"])
    # Quit the tray icon
    icon.stop()

def on_quit(icon, item):
    icon.stop()

def get_menu():
    status = get_status()
    status_text = "Active" if status else "Disabled"
    return pystray.Menu(
        pystray.MenuItem(f"Status: {status_text}", lambda: None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Toggle Adblocking", on_toggle),
        pystray.MenuItem("Open Settings", on_open_settings),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Hide Indicator (Keep running)", on_quit),
        pystray.MenuItem("Stop Service & Exit", on_stop_and_quit)
    )

def setup_icon():
    status = get_status()
    color = "green" if status else "red"
    icon = pystray.Icon("DNS66", create_image(color), "DNS66 Client", menu=get_menu())
    return icon

def update_loop(icon):
    last_status = get_status()
    while icon.visible:
        time.sleep(2)
        current_status = get_status()
        if current_status != last_status:
            last_status = current_status
            color = "green" if current_status else "red"
            icon.icon = create_image(color)
            icon.menu = get_menu()
            icon.update_menu()

def main():
    icon = setup_icon()
    icon.visible = True
    
    # Start background thread to poll config file for updates (so tray stays in sync if changed via UI)
    t = threading.Thread(target=update_loop, args=(icon,))
    t.daemon = True
    t.start()
    
    icon.run()

if __name__ == "__main__":
    main()
