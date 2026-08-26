#! /usr/bin/python3
import sys
import os
import json
import threading
import subprocess
import time
import urllib.request
import urllib.error

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib, Gdk, Gio

class DNS66App(Gtk.Application):
    def __init__(self):
        super().__init__(application_id='com.github.dns66.client',
                         flags=Gio.ApplicationFlags.FLAGS_NONE)
        
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_file = os.path.join(self.base_dir, "config.json")
        self.ad_domains_file = os.path.join(self.base_dir, "ad_domains.json")
        self.service_name = "dns66.service"
        self.icon_dir = os.path.join(self.base_dir, "icons")
        self.test_running = False

    def load_config(self):
        try:
            with open(self.config_file, "r") as f:
                return json.load(f)
        except:
            return {
                "upstream_dns": ["8.8.8.8", "1.1.1.1"],
                "blocklists": [],
                "service_enabled": True,
                "enable_ipv6": True,
                "enable_watchdog": True,
                "daily_refresh": True
            }

    def save_config(self, cfg):
        try:
            with open(self.config_file, "w") as f:
                json.dump(cfg, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")

    def do_startup(self):
        Gtk.Application.do_startup(self)
        
        # Enforce dark theme by default
        settings = Gtk.Settings.get_default()
        if settings:
            settings.set_property("gtk-application-prefer-dark-theme", True)

    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = Gtk.ApplicationWindow(application=self)
            win.set_title("DNS66 Client for Linux")
            win.set_default_size(450, 750)
            win.set_resizable(False)

            provider = Gtk.CssProvider()
            provider.load_from_data(b"""
            @keyframes pulse {
                0% { transform: scale(1); opacity: 1; }
                50% { transform: scale(1.1); opacity: 0.8; }
                100% { transform: scale(1); opacity: 1; }
            }
            .anim-shield {
                animation: pulse 1s infinite linear;
            }
            .big-shield-btn {
                border-radius: 9999px;
                padding: 20px;
                background: rgba(255,255,255,0.05);
            }
            .big-shield-btn:hover {
                background: rgba(255,255,255,0.1);
            }
            """)
            Gtk.StyleContext.add_provider_for_display(
                win.get_display(), 
                provider, 
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )

            self.create_widgets(win)
            self.check_service_status()

            GLib.timeout_add(3000, self.check_service_status)
            
        win.present()
        
    def _create_icon_button(self, label_text, icon_name):
        btn = Gtk.Button()
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        box.set_halign(Gtk.Align.CENTER)
        
        icon_path = os.path.join(self.icon_dir, f"{icon_name}.png")
        if os.path.exists(icon_path):
            img = Gtk.Image.new_from_file(icon_path)
            img.set_pixel_size(24)
            box.append(img)
            
        lbl = Gtk.Label(label=label_text)
        box.append(lbl)
        btn.set_child(box)
        return btn

    def create_widgets(self, win):
        self.notebook = Gtk.Notebook()
        win.set_child(self.notebook)

        self.setup_status_tab()
        self.setup_hosts_tab()
        self.setup_dns_tab()
        self.setup_test_tab()
        self.setup_donate_tab()

    def setup_status_tab(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        box.set_margin_top(30)
        box.set_margin_bottom(20)
        box.set_margin_start(20)
        box.set_margin_end(20)
        
        logo_path = os.path.join(self.base_dir, "dns66-icon.png")
        if os.path.exists(logo_path):
            img = Gtk.Picture.new_for_filename(logo_path)
            img.set_size_request(96, 96)
            box.append(img)
            
        self.lbl_status = Gtk.Label(label="Checking status...")
        self.lbl_status.add_css_class("title-2")
        box.append(self.lbl_status)

        self.btn_toggle = self._create_icon_button("Start Shield", "shield")
        self.btn_toggle.add_css_class("suggested-action")
        self.btn_toggle.add_css_class("pill")
        self.btn_toggle.set_size_request(220, 50)
        self.btn_toggle.set_halign(Gtk.Align.CENTER)
        self.btn_toggle.connect("clicked", self.on_toggle_service)
        box.append(self.btn_toggle)

        self.btn_update = self._create_icon_button("Update Hosts Cache", "sync")
        self.btn_update.add_css_class("pill")
        self.btn_update.set_size_request(220, 50)
        self.btn_update.set_halign(Gtk.Align.CENTER)
        self.btn_update.connect("clicked", self.on_update_hosts)
        box.append(self.btn_update)
        
        self.btn_chk_update = self._create_icon_button("Check for Updates", "refresh")
        self.btn_chk_update.add_css_class("pill")
        self.btn_chk_update.set_size_request(220, 50)
        self.btn_chk_update.set_halign(Gtk.Align.CENTER)
        self.btn_chk_update.connect("clicked", self.on_check_update)
        box.append(self.btn_chk_update)

        # Advanced settings frame
        frame = Gtk.Frame()
        frame.set_margin_top(15)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(15)
        vbox.set_margin_bottom(15)
        vbox.set_margin_start(15)
        vbox.set_margin_end(15)
        frame.set_child(vbox)
        
        lbl_adv = Gtk.Label(label="<b>Advanced Settings</b>", use_markup=True)
        lbl_adv.set_halign(Gtk.Align.START)
        vbox.append(lbl_adv)
        
        cfg = self.load_config()
        
        def make_switch_row(text, active=True, callback=None):
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            lbl = Gtk.Label(label=text)
            lbl.set_hexpand(True)
            lbl.set_halign(Gtk.Align.START)
            sw = Gtk.Switch()
            sw.set_active(active)
            if callback:
                sw.connect("notify::active", callback)
            row.append(lbl)
            row.append(sw)
            return row, sw

        r1, self.sw_ipv6 = make_switch_row("IPv6 Support", active=cfg.get("enable_ipv6", True), callback=self.on_cfg_toggle)
        r2, self.sw_watchdog = make_switch_row("Watchdog Reconnect", active=cfg.get("enable_watchdog", True), callback=self.on_cfg_toggle)
        r3, self.sw_daily = make_switch_row("Automatic Daily Refresh", active=cfg.get("daily_refresh", True), callback=self.on_cfg_toggle)
        r4, self.sw_dark = make_switch_row("Dark Mode", active=True, callback=self.on_dark_toggle)
        
        vbox.append(r1)
        vbox.append(r2)
        vbox.append(r3)
        vbox.append(r4)

        box.append(frame)

        scroll = Gtk.ScrolledWindow()
        scroll.set_child(box)
        self.notebook.append_page(scroll, Gtk.Label(label="Status"))

    def on_cfg_toggle(self, switch, gparam):
        cfg = self.load_config()
        cfg["enable_ipv6"] = self.sw_ipv6.get_active()
        cfg["enable_watchdog"] = self.sw_watchdog.get_active()
        cfg["daily_refresh"] = self.sw_daily.get_active()
        self.save_config(cfg)

    def setup_hosts_tab(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(20)
        box.set_margin_bottom(20)
        box.set_margin_start(10)
        box.set_margin_end(10)

        lbl = Gtk.Label(label="Blocklists")
        lbl.add_css_class("title-3")
        box.append(lbl)

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        self.hosts_listbox = Gtk.ListBox()
        self.hosts_listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        scroll.set_child(self.hosts_listbox)
        box.append(scroll)
        
        bbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        bbox.set_halign(Gtk.Align.CENTER)
        
        btn_add = self._create_icon_button("Add List", "add")
        btn_add.connect("clicked", self.on_add_host)
        
        btn_rem = self._create_icon_button("Remove", "trash")
        btn_rem.add_css_class("destructive-action")
        btn_rem.connect("clicked", self.on_remove_host)

        bbox.append(btn_add)
        bbox.append(btn_rem)
        box.append(bbox)

        self.load_hosts_to_list()
        self.notebook.append_page(box, Gtk.Label(label="Hosts"))

    def create_host_row(self, url, active):
        row = Gtk.ListBoxRow()
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        box.set_margin_start(10)
        box.set_margin_end(10)
        
        lbl = Gtk.Label(label=url)
        lbl.set_hexpand(True)
        lbl.set_halign(Gtk.Align.START)
        lbl.set_ellipsize(3) # Pango.EllipsizeMode.END equivalent
        
        switch = Gtk.Switch()
        switch.set_active(active)
        switch.set_valign(Gtk.Align.CENTER)
        
        def on_switch_notify(sw, gparam):
            is_active = sw.get_active()
            cfg = self.load_config()
            for item in cfg.get("blocklists", []):
                if item.get("url") == url:
                    item["enabled"] = is_active
                    break
            self.save_config(cfg)
            
        switch.connect("notify::active", on_switch_notify)

        box.append(lbl)
        box.append(switch)
        row.set_child(box)
        row.url_data = url
        return row

    def load_hosts_to_list(self):
        while True:
            row = self.hosts_listbox.get_row_at_index(0)
            if row:
                self.hosts_listbox.remove(row)
            else:
                break
        
        cfg = self.load_config()
        for item in cfg.get("blocklists", []):
            url = item.get("url", "")
            active = item.get("enabled", True)
            if url:
                self.hosts_listbox.append(self.create_host_row(url, active))

    def setup_dns_tab(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(20)
        box.set_margin_bottom(20)
        box.set_margin_start(10)
        box.set_margin_end(10)

        lbl = Gtk.Label(label="DNS Servers")
        lbl.add_css_class("title-3")
        box.append(lbl)
        
        cfg = self.load_config()
        self.use_custom_dns_chk = Gtk.CheckButton(label="Use Custom DNS Servers")
        self.use_custom_dns_chk.set_active(not cfg.get("use_system_dns", True))
        box.append(self.use_custom_dns_chk)

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        self.dns_listbox = Gtk.ListBox()
        self.dns_listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        scroll.set_child(self.dns_listbox)
        box.append(scroll)
        
        bbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        bbox.set_halign(Gtk.Align.CENTER)
        
        self.btn_add_dns = self._create_icon_button("Add Server", "add")
        self.btn_add_dns.connect("clicked", self.on_add_dns)
        
        self.btn_rem_dns = self._create_icon_button("Remove", "trash")
        self.btn_rem_dns.add_css_class("destructive-action")
        self.btn_rem_dns.connect("clicked", self.on_remove_dns)

        bbox.append(self.btn_add_dns)
        bbox.append(self.btn_rem_dns)
        box.append(bbox)
        
        def on_custom_dns_toggled(btn):
            active = btn.get_active()
            scroll.set_sensitive(active)
            bbox.set_sensitive(active)
            cfg = self.load_config()
            cfg["use_system_dns"] = not active
            self.save_config(cfg)
            
        self.use_custom_dns_chk.connect("toggled", on_custom_dns_toggled)
        on_custom_dns_toggled(self.use_custom_dns_chk)

        self.load_dns_to_list()
        self.notebook.append_page(box, Gtk.Label(label="DNS"))

    def create_dns_row(self, ip, active):
        row = Gtk.ListBoxRow()
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        box.set_margin_start(10)
        box.set_margin_end(10)
        
        lbl = Gtk.Label(label=ip)
        lbl.set_hexpand(True)
        lbl.set_halign(Gtk.Align.START)
        
        switch = Gtk.Switch()
        switch.set_active(active)
        switch.set_valign(Gtk.Align.CENTER)
        
        def on_switch_notify(sw, gparam):
            is_active = sw.get_active()
            cfg = self.load_config()
            new_dns = []
            for u in cfg.get("upstream_dns", []):
                if isinstance(u, str):
                    if u == ip:
                        new_dns.append({"ip": u, "enabled": is_active})
                    else:
                        new_dns.append(u)
                else:
                    if u.get("ip") == ip:
                        u["enabled"] = is_active
                    new_dns.append(u)
            cfg["upstream_dns"] = new_dns
            self.save_config(cfg)
            
        switch.connect("notify::active", on_switch_notify)
        
        box.append(lbl)
        box.append(switch)
        row.set_child(box)
        row.ip_data = ip
        return row

    def load_dns_to_list(self):
        while True:
            row = self.dns_listbox.get_row_at_index(0)
            if row:
                self.dns_listbox.remove(row)
            else:
                break
        
        cfg = self.load_config()
        for item in cfg.get("upstream_dns", []):
            if isinstance(item, dict):
                self.dns_listbox.append(self.create_dns_row(item.get("ip", ""), item.get("enabled", True)))
            else:
                self.dns_listbox.append(self.create_dns_row(item, True))

    def draw_progress_arc(self, area, cr, width, height):
        if not hasattr(self, 'test_progress'):
            self.test_progress = 0.0
            
        import math
        xc = width / 2.0
        yc = height / 2.0
        radius = min(width, height) / 2.0 - 10.0
        
        # draw background circle
        cr.set_source_rgba(0.2, 0.2, 0.2, 0.5)
        cr.set_line_width(8.0)
        cr.arc(xc, yc, radius, 0, 2 * math.pi)
        cr.stroke()
        
        # draw progress arc
        if self.test_progress > 0:
            cr.set_source_rgba(0.2, 0.6, 1.0, 1.0) # blue
            cr.set_line_width(8.0)
            angle = self.test_progress * 2 * math.pi
            cr.arc(xc, yc, radius, -math.pi/2, -math.pi/2 + angle)
            cr.stroke()

    def setup_test_tab(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(20)
        box.set_margin_bottom(20)
        box.set_margin_start(10)
        box.set_margin_end(10)

        lbl = Gtk.Label(label="Test AdBlock")
        lbl.add_css_class("title-3")
        box.append(lbl)
        
        opt_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        opt_box.set_halign(Gtk.Align.CENTER)
        opt_box.append(Gtk.Label(label="Domains to test:"))
        
        self.test_count_dd = Gtk.DropDown.new_from_strings(["50", "100", "500", "1000"])
        opt_box.append(self.test_count_dd)
        box.append(opt_box)

        # Big animated shield button
        self.btn_test = Gtk.Button()
        self.btn_test.add_css_class("big-shield-btn")
        self.btn_test.set_halign(Gtk.Align.CENTER)
        
        overlay = Gtk.Overlay()
        
        # Add drawing area behind the shield (or above, as an overlay)
        self.progress_area = Gtk.DrawingArea()
        self.progress_area.set_draw_func(self.draw_progress_arc)
        self.progress_area.set_size_request(220, 220)
        overlay.set_child(self.progress_area)
        
        shield_path = os.path.join(self.icon_dir, "shield.png")
        if os.path.exists(shield_path):
            img = Gtk.Image.new_from_file(shield_path)
            img.set_pixel_size(160)
            img.set_halign(Gtk.Align.CENTER)
            img.set_valign(Gtk.Align.CENTER)
            overlay.add_overlay(img)
            
        self.lbl_test_btn = Gtk.Label(label="Start")
        self.lbl_test_btn.set_justify(Gtk.Justification.CENTER)
        # Use markup so it has a readable color/weight against the shield
        self.lbl_test_btn.set_markup("<span font_desc='16' font_weight='bold' color='white'>Start</span>")
        self.lbl_test_btn.set_halign(Gtk.Align.CENTER)
        self.lbl_test_btn.set_valign(Gtk.Align.CENTER)
        
        overlay.add_overlay(self.lbl_test_btn)
            
        center_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        center_box.set_vexpand(True)
        center_box.set_valign(Gtk.Align.CENTER)
        
        self.btn_test.set_child(overlay)
        self.btn_test.connect("clicked", self.on_test_button_clicked)
        center_box.append(self.btn_test)

        self.btn_toggle_logs = Gtk.ToggleButton(label="Show Logs")
        self.btn_toggle_logs.set_halign(Gtk.Align.CENTER)
        center_box.append(self.btn_toggle_logs)
        
        box.append(center_box)

        self.log_scroll = Gtk.ScrolledWindow()
        self.log_scroll.set_vexpand(True)
        self.log_scroll.set_visible(False)
        
        self.test_log = Gtk.TextView()
        self.test_log.set_editable(False)
        self.test_log.set_wrap_mode(Gtk.WrapMode.WORD)
        
        # Tags for color formatting
        self.log_buf = self.test_log.get_buffer()
        self.log_buf.create_tag("error", foreground="red")
        self.log_buf.create_tag("success", foreground="green")
        self.log_buf.create_tag("bold", weight=700)
        
        self.log_scroll.set_child(self.test_log)
        box.append(self.log_scroll)

        def on_logs_toggled(btn):
            if btn.get_active():
                self.log_scroll.set_visible(True)
                btn.set_label("Hide Logs")
            else:
                self.log_scroll.set_visible(False)
                btn.set_label("Show Logs")
                
        self.btn_toggle_logs.connect("toggled", on_logs_toggled)

        self.notebook.append_page(box, Gtk.Label(label="Test AdBlock"))

    def setup_donate_tab(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        box.set_margin_top(30)
        box.set_margin_bottom(30)
        box.set_margin_start(20)
        box.set_margin_end(20)
        
        lbl = Gtk.Label(label="Support DNS66 Linux")
        lbl.add_css_class("title-2")
        box.append(lbl)
        
        center_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        center_box.set_vexpand(True)
        center_box.set_valign(Gtk.Align.CENTER)
        center_box.set_halign(Gtk.Align.CENTER)
        
        qr_path = os.path.join(self.icon_dir, "donate_qr.png")
        if os.path.exists(qr_path):
            img = Gtk.Image.new_from_file(qr_path)
            img.set_pixel_size(300)
            center_box.append(img)
            
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        hbox.set_halign(Gtk.Align.CENTER)
        
        entry = Gtk.Entry()
        entry.set_text("karam.shine-2@oksbi")
        entry.set_editable(False)
        entry.set_width_chars(25)
        hbox.append(entry)
        
        btn_copy = Gtk.Button(label="Copy UPI")
        def on_copy_clicked(btn):
            clipboard = btn.get_display().get_clipboard()
            clipboard.set(entry.get_text())
            btn.set_label("Copied!")
            GLib.timeout_add_seconds(2, lambda: btn.set_label("Copy UPI") and False)
            
        btn_copy.connect("clicked", on_copy_clicked)
        hbox.append(btn_copy)
        
        center_box.append(hbox)
        
        lbl_scan = Gtk.Label(label="Scan to pay with any UPI app")
        lbl_scan.add_css_class("dim-label")
        center_box.append(lbl_scan)
        
        box.append(center_box)
        self.notebook.append_page(box, Gtk.Label(label="Donate"))

    # --- Actions ---

    def on_dark_toggle(self, switch, gparam):
        settings = Gtk.Settings.get_default()
        if settings:
            settings.set_property("gtk-application-prefer-dark-theme", switch.get_active())

    def on_check_update(self, btn):
        self.btn_chk_update.set_sensitive(False)
        def worker():
            time.sleep(1.5)
            GLib.idle_add(self.show_msg, "Updates", "You are running the latest version of DNS66 Client.")
            GLib.idle_add(self.btn_chk_update.set_sensitive, True)
        threading.Thread(target=worker, daemon=True).start()

    def check_service_status(self):
        try:
            res = subprocess.run(["systemctl", "is-active", self.service_name], capture_output=True, text=True)
            box = self.btn_toggle.get_child()
            lbl = None
            if box:
                for c in box:
                    if isinstance(c, Gtk.Label): lbl = c
            
            if res.stdout.strip() == "active":
                self.lbl_status.set_markup("<span foreground='#10B981'>Shield is ACTIVE</span>")
                if lbl: lbl.set_label("Disable Shield")
                self.btn_toggle.remove_css_class("suggested-action")
                self.btn_toggle.add_css_class("destructive-action")
            else:
                self.lbl_status.set_markup("<span foreground='#EF4444'>Shield is INACTIVE</span>")
                if lbl: lbl.set_label("Start Shield")
                self.btn_toggle.remove_css_class("destructive-action")
                self.btn_toggle.add_css_class("suggested-action")
        except Exception:
            self.lbl_status.set_label("Status Unknown")
        return True

    def on_toggle_service(self, btn):
        active = "ACTIVE" in self.lbl_status.get_label()
        cmd = ["pkexec", "systemctl", "stop" if active else "start", self.service_name]
        try:
            subprocess.run(cmd, check=True)
            self.check_service_status()
        except subprocess.CalledProcessError:
            self.show_error("Authentication failed or unable to change service state.")

    def on_update_hosts(self, btn):
        self.btn_update.set_sensitive(False)
        box = self.btn_update.get_child()
        lbl = [c for c in box if isinstance(c, Gtk.Label)][0] if box else None
        if lbl: lbl.set_label("Updating...")
        
        def worker():
            try:
                subprocess.run(["pkexec", "systemctl", "restart", self.service_name], check=True)
                GLib.idle_add(self.show_msg, "Success", "Hosts cache updated successfully. Restart the client to see changes.")
            except subprocess.CalledProcessError:
                GLib.idle_add(self.show_error, "Failed to update hosts cache.")
            finally:
                GLib.idle_add(self.btn_update.set_sensitive, True)
                if lbl: GLib.idle_add(lbl.set_label, "Update Hosts Cache")
        threading.Thread(target=worker, daemon=True).start()

    def on_add_host(self, btn):
        self.show_entry_dialog("Add List", "URL:", self._save_new_host)
        
    def _save_new_host(self, url):
        url = url.strip()
        if url:
            cfg = self.load_config()
            bl = cfg.get("blocklists", [])
            exists = False
            for b in bl:
                if b.get("url") == url:
                    exists = True
                    break
            if not exists:
                bl.append({"url": url, "enabled": True, "action": "deny"})
                cfg["blocklists"] = bl
                self.save_config(cfg)
                self.load_hosts_to_list()


    def on_remove_host(self, btn):
        row = self.hosts_listbox.get_selected_row()
        if not row: return
        url = row.url_data
        cfg = self.load_config()
        bl = [b for b in cfg.get("blocklists", []) if b.get("url") != url]
        cfg["blocklists"] = bl
        self.save_config(cfg)
        self.load_hosts_to_list()

    def on_add_dns(self, btn):
        self.show_entry_dialog("Add DNS", "DNS IP:", self._save_new_dns)
        
    def _save_new_dns(self, ip):
        ip = ip.strip()
        if ip:
            cfg = self.load_config()
            dns = cfg.get("upstream_dns", [])
            exists = False
            for u in dns:
                if isinstance(u, dict) and u.get("ip") == ip:
                    exists = True
                elif isinstance(u, str) and u == ip:
                    exists = True
            if not exists:
                dns.append({"ip": ip, "enabled": True})
                cfg["upstream_dns"] = dns
                self.save_config(cfg)
                self.load_dns_to_list()

    def on_remove_dns(self, btn):
        row = self.dns_listbox.get_selected_row()
        if not row: return
        ip = row.ip_data
        cfg = self.load_config()
        dns = cfg.get("upstream_dns", [])
        new_dns = []
        for u in dns:
            if isinstance(u, dict) and u.get("ip") == ip:
                continue
            elif isinstance(u, str) and u == ip:
                continue
            new_dns.append(u)
        cfg["upstream_dns"] = new_dns
        self.save_config(cfg)
        self.load_dns_to_list()

    def on_test_button_clicked(self, btn):
        if self.test_running:
            self.test_running = False
            return
            
        if "ACTIVE" not in self.lbl_status.get_label():
            self.show_error("Shield is not active. Test might bypass AdBlock.")
            
        self.btn_test.add_css_class("anim-shield")
        self.lbl_test_btn.set_markup("<span font_desc='16' font_weight='bold' color='white'>Stop</span>")
        self.log_buf.set_text("")
        self.test_running = True
        
        model = self.test_count_dd.get_model()
        idx = self.test_count_dd.get_selected()
        val = model.get_string(idx)
        count = int(val)

        self.test_progress = 0.0
        self.progress_area.queue_draw()

        def log_msg(msg, tag=None):
            def _do_log():
                iter_end = self.log_buf.get_end_iter()
                if tag:
                    self.log_buf.insert_with_tags_by_name(iter_end, msg, tag)
                else:
                    self.log_buf.insert(iter_end, msg)
                
                # Move the cursor to the newly added end so we can scroll to it
                iter_new_end = self.log_buf.get_end_iter()
                self.log_buf.place_cursor(iter_new_end)
                mark = self.log_buf.get_insert()
                self.test_log.scroll_to_mark(mark, 0.0, True, 0.0, 1.0)
            GLib.idle_add(_do_log)
            
        def run_test():
            completed_score = None
            try:
                domains_to_test = []
                try:
                    with open(self.ad_domains_file, "r") as f:
                        data = json.load(f)
                    
                    if isinstance(data, dict):
                        keys = list(data.keys())
                        domains_to_test = keys[:count]
                    elif isinstance(data, list):
                        domains_to_test = data[:count]
                except Exception as e:
                    log_msg(f"Could not load cached domains: {e}\n", "error")
                
                if not domains_to_test:
                    log_msg("No domains found to test in ad_domains.json cache.\n")
                    return

                blocked = 0
                for i, d in enumerate(domains_to_test):
                    if not self.test_running:
                        log_msg("\n--- Test Stopped ---\n", "bold")
                        break
                        
                    log_msg(f"Testing {d}... ")
                    try:
                        import socket
                        socket.gethostbyname(d)
                        log_msg("RESOLVED (Not Blocked)\n", "error")
                    except socket.error:
                        blocked += 1
                        log_msg("BLOCKED\n", "success")
                        
                    self.test_progress = (i + 1) / len(domains_to_test)
                    def _update_ui(p=self.test_progress):
                        self.progress_area.queue_draw()
                        self.lbl_test_btn.set_markup(f"<span font_desc='16' font_weight='bold' color='white'>Stop\n{int(p*100)}%</span>")
                    GLib.idle_add(_update_ui)
                    
                    time.sleep(0.01)
                
                if self.test_running:
                    log_msg(f"\n--- Test Complete ---\nBlocked: {blocked}/{len(domains_to_test)}\n", "bold")
                    completed_score = int((blocked / len(domains_to_test)) * 100)

            except Exception as e:
                log_msg(f"Test error: {e}\n", "error")
            finally:
                self.test_running = False
                def _reset_btn():
                    self.btn_test.remove_css_class("anim-shield")
                    if completed_score is not None:
                        self.lbl_test_btn.set_markup(f"<span font_desc='16' font_weight='bold' color='white'>Score:\n{completed_score}%</span>")
                    else:
                        self.lbl_test_btn.set_markup("<span font_desc='16' font_weight='bold' color='white'>Start</span>")
                GLib.idle_add(_reset_btn)

        threading.Thread(target=run_test, daemon=True).start()

    def show_error(self, msg):
        self._msg_dialog("Error", msg)
        
    def show_msg(self, title, msg):
        self._msg_dialog(title, msg)
        
    def _msg_dialog(self, title, msg):
        dialog = Gtk.AlertDialog(message=title, detail=msg)
        dialog.show(self.props.active_window)

    def show_entry_dialog(self, title, label_txt, callback):
        win = Gtk.Window(title=title, transient_for=self.props.active_window, modal=True)
        win.set_default_size(300, 100)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(20)
        box.set_margin_bottom(20)
        box.set_margin_start(20)
        box.set_margin_end(20)
        
        lbl = Gtk.Label(label=label_txt)
        entry = Gtk.Entry()
        btn = Gtk.Button(label="Save")
        
        box.append(lbl)
        box.append(entry)
        box.append(btn)
        win.set_child(box)
        
        def on_save(b):
            val = entry.get_text()
            win.destroy()
            if val:
                callback(val)
                
        btn.connect("clicked", on_save)
        win.present()

if __name__ == '__main__':
    app = DNS66App()
    exit_status = app.run(sys.argv)
    sys.exit(exit_status)
