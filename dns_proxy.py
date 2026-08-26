#!/usr/bin/env python3
import json
import os
import socket
import threading
import urllib.request
import time
import sys
from dnslib import DNSRecord, DNSHeader, RR, A, QTYPE

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cache')

blocked_domains = set()
allowed_domains = set()
config = {}

def load_config():
    global config
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        config = {"upstream_dns": ["8.8.8.8"], "blocklists": [], "service_enabled": True}

def update_hagezi_catalog():
    print("Fetching Hagezi catalog from GitHub API...")
    try:
        req = urllib.request.Request("https://api.github.com/repos/hagezi/dns-blocklists/git/trees/main?recursive=1", headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            tree_data = json.loads(response.read().decode('utf-8'))
            
            existing_urls = {bl.get('url') for bl in config.get('blocklists', [])}
            added = False
            
            for item in tree_data.get('tree', []):
                path = item.get('path', '')
                if path.startswith('adblock/') and path.endswith('.txt'):
                    url = f"https://raw.githubusercontent.com/hagezi/dns-blocklists/main/{path}"
                    if url not in existing_urls:
                        config.setdefault('blocklists', []).append({
                            "url": url,
                            "enabled": False,
                            "action": "deny"
                        })
                        added = True
            
            if added:
                print("New Hagezi lists found. Updating config.json...")
                with open(CONFIG_FILE, 'w') as f:
                    json.dump(config, f, indent=2)
    except Exception as e:
        print(f"Failed to fetch Hagezi catalog: {e}")

def download_hosts():
    print("Downloading hosts...")
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
    
    for bl in config.get('blocklists', []):
        if bl.get('enabled', True) and bl.get('action', 'deny') != 'ignore':
            # Create a safe filename from the URL
            safe_name = bl['url'].replace('https://', '').replace('http://', '').replace('/', '_') + '.txt'
            cache_path = os.path.join(CACHE_DIR, safe_name)
            try:
                print(f"Fetching {bl['url']}")
                req = urllib.request.Request(bl['url'], headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=10) as response:
                    content = response.read().decode('utf-8')
                    with open(cache_path, 'w') as f:
                        f.write(content)
            except Exception as e:
                print(f"Failed to fetch {bl['url']}: {e}")
    print("Hosts downloaded.")

def load_blocked_domains():
    global blocked_domains, allowed_domains
    blocked_domains.clear()
    allowed_domains.clear()
    
    # Check if we need to download
    cache_empty = True
    if os.path.exists(CACHE_DIR) and os.listdir(CACHE_DIR):
        cache_empty = False
        
    if cache_empty:
        download_hosts()
        
    for bl in config.get('blocklists', []):
        if not bl.get('enabled', True):
            continue
            
        action = bl.get('action', 'deny')
        if action == 'ignore':
            continue
            
        safe_name = bl['url'].replace('https://', '').replace('http://', '').replace('/', '_') + '.txt'
        cache_path = os.path.join(CACHE_DIR, safe_name)
        
        if not os.path.exists(cache_path):
            continue
            
        try:
            with open(cache_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#') or line.startswith('!'):
                        continue
                        
                    domain = None
                    parts = line.split()
                    
                    # Adblock format (||example.com^)
                    if line.startswith("||") and line.endswith("^"):
                        domain = line[2:-1].lower()
                    # Hosts format (0.0.0.0 example.com)
                    elif len(parts) >= 2 and parts[0] in ('0.0.0.0', '127.0.0.1'):
                        domain = parts[1].lower()
                    # Raw domain list format (example.com)
                    elif len(parts) == 1 and '.' in line:
                        domain = parts[0].lower()
                        
                    if domain:
                        if action == 'allow':
                            allowed_domains.add(domain)
                        else:
                            blocked_domains.add(domain)
        except Exception as e:
            print(f"Error loading {cache_path}: {e}")
            
    print(f"Loaded {len(blocked_domains)} blocked domains and {len(allowed_domains)} allowed domains.")

def forward_dns(data, upstream_ip, port=53):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2.0)
        sock.sendto(data, (upstream_ip, port))
        response, _ = sock.recvfrom(4096)
        sock.close()
        return response
    except Exception as e:
        # Avoid spamming errors on watchdog pings if network is temporarily down
        return None

def get_system_dns():
    locations = [
        "/run/systemd/resolve/resolv.conf",
        "/run/NetworkManager/resolv.conf",
        "/etc/resolv.conf.dns66.bak"
    ]
    servers = []
    for loc in locations:
        if os.path.exists(loc):
            try:
                with open(loc, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("nameserver "):
                            ip = line.split()[1]
                            if ip not in ["127.0.0.1", "127.0.0.53", "::1"]:
                                servers.append(ip)
            except:
                pass
            if servers:
                return servers
    return []

def get_configured_upstreams():
    raw_upstreams = config.get('upstream_dns', ['8.8.8.8'])
    upstreams = []
    for u in raw_upstreams:
        if isinstance(u, dict):
            if u.get('enabled', True):
                upstreams.append(u.get('ip', ''))
        else:
            upstreams.append(u)
    return [u for u in upstreams if u]

def handle_request(data, addr, sock):
    try:
        request = DNSRecord.parse(data)
        qname = str(request.q.qname).strip('.').lower()
        
        if not config.get('service_enabled', True):
            pass # Filtering disabled
        elif qname in allowed_domains:
            pass # Allowed by per-host rule
        elif qname in blocked_domains:
            reply = request.reply()
            reply.add_answer(RR(request.q.qname, QTYPE.A, rdata=A("0.0.0.0"), ttl=60))
            sock.sendto(reply.pack(), addr)
            return

        # Forward request to upstream
        upstreams = []
        if config.get('use_system_dns', True):
            upstreams = get_system_dns()
        
        if not upstreams:
            upstreams = get_configured_upstreams()
            if not upstreams:
                upstreams = ['8.8.8.8']
            
        for upstream in upstreams:
            response = forward_dns(data, upstream)
            if response:
                sock.sendto(response, addr)
                return
    except Exception as e:
        print(f"Error handling request: {e}")

def serve_udp(ip, port, family):
    try:
        sock = socket.socket(family, socket.SOCK_DGRAM)
        sock.bind((ip, port))
        print(f"Listening on {ip}:{port}...")
        while True:
            data, addr = sock.recvfrom(4096)
            threading.Thread(target=handle_request, args=(data, addr, sock)).start()
    except Exception as e:
        print(f"Failed to bind/listen on {ip}:{port}: {e}")

def daily_refresh_thread():
    while config.get('daily_refresh', True):
        # 86400 seconds = 24 hours
        time.sleep(86400)
        print("Running automatic daily refresh...")
        update_hagezi_catalog()
        download_hosts()
        load_blocked_domains()

def watchdog_thread():
    # Test query: example.com
    test_query = DNSRecord.question("example.com").pack()
    failures = 0
    while config.get('enable_watchdog', True):
        time.sleep(60)
        upstreams = []
        if config.get('use_system_dns', True):
            upstreams = get_system_dns()
        if not upstreams:
            upstreams = get_configured_upstreams()
            if not upstreams:
                upstreams = ['8.8.8.8']
            
        success = False
        for upstream in upstreams:
            if forward_dns(test_query, upstream):
                success = True
                break
                
        if success:
            failures = 0
        else:
            failures += 1
            print(f"Watchdog: Upstream connection failed. Failures: {failures}")
            if failures >= 3:
                print("Watchdog: 3 consecutive failures. Restarting process to recover.")
                os._exit(1) # Force exit to trigger systemd Restart=on-failure

def main():
    load_config()
    load_blocked_domains()
    
    # Start background tasks
    if config.get('daily_refresh', True):
        threading.Thread(target=daily_refresh_thread, daemon=True).start()
        
    if config.get('enable_watchdog', True):
        threading.Thread(target=watchdog_thread, daemon=True).start()
    
    # Start listeners
    threads = []
    
    # IPv4
    t_ipv4 = threading.Thread(target=serve_udp, args=("127.0.0.1", 53, socket.AF_INET))
    t_ipv4.daemon = True
    t_ipv4.start()
    threads.append(t_ipv4)
    
    # IPv6
    if config.get('enable_ipv6', True):
        t_ipv6 = threading.Thread(target=serve_udp, args=("::1", 53, socket.AF_INET6))
        t_ipv6.daemon = True
        t_ipv6.start()
        threads.append(t_ipv6)
        
    # Wait for listeners
    for t in threads:
        t.join()

if __name__ == "__main__":
    main()
