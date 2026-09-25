# DNS66 Architecture

## Overview
DNS66 is divided into three distinct operational layers: the Core Proxy, the GUI, and the System Integration layer.

## 1. Core Proxy (`dns_proxy.py`)
This is the heart of the application. It runs as a root-privileged daemon.
- **DNS Handling:** Uses `dnslib` to listen on UDP port 53 (IPv4 and IPv6).
- **Filtering Logic:** Parses lists of known malicious/ad domains and stores them in memory.
- **Resolution:** If a domain is on the blocklist, it returns `0.0.0.0`. Otherwise, it forwards the query to the upstream DNS (e.g., `8.8.8.8` or the system's default).

## 2. User Interface (`ui.py` & `tray.py`)
- **Tkinter GUI:** A lightweight, dependency-free Python GUI used to manage blocklists (Add/Remove/Enable/Disable).
- **Authentication:** Since editing DNS requires root access, the UI triggers `pkexec` when it needs to apply system-wide changes.
- **Tray Applet:** A background icon in the Linux system tray for quick toggling and status monitoring.

## 3. System Integration (`systemd-resolved`)
- The proxy integrates with `systemd-resolved` to ensure all system networking traffic is properly routed through `127.0.0.1:53` without disrupting standard network connections.
