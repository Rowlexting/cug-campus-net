import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import json
import os
import sys
import requests
from datetime import datetime
from PIL import Image, ImageDraw
import pystray
from srun_login import srun_login

# ========= 路径 =========
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")


def load_config():
    """加载配置"""
    default = {"username": "", "password": "", "interval": 60}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                default.update(saved)
        except Exception:
            pass
    return default


def save_config(config):
    """保存配置"""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def is_online():
    """检测是否在线"""
    try:
        resp = requests.get("http://www.baidu.com", timeout=5)
        if resp.status_code == 200 and "192.168.167.115" not in resp.url and "nap.cug.edu.cn" not in resp.url:
            return True
    except requests.RequestException:
        pass
    return False


def reconnect(username, password, headless=True):
    """重新连接校园网（纯 requests，无需浏览器）"""
    return srun_login(username, password)


def create_tray_icon():
    """创建一个简单的托盘图标"""
    img = Image.new('RGB', (64, 64), color=(34, 139, 34))
    draw = ImageDraw.Draw(img)
    draw.ellipse([12, 12, 52, 52], fill=(255, 255, 255))
    draw.ellipse([20, 20, 44, 44], fill=(34, 139, 34))
    return img


class KeepAliveApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("CUG校园网保活工具")
        self.root.geometry("420x480")
        self.root.resizable(False, False)

        self.running = False
        self.thread = None
        self.config = load_config()
        self.tray_icon = None

        self.build_ui()
        self.load_ui_from_config()

        # 点击关闭按钮时最小化到托盘
        self.root.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)

    def build_ui(self):
        # 账号密码区
        frame_account = ttk.LabelFrame(self.root, text="账号设置", padding=10)
        frame_account.pack(fill="x", padx=10, pady=(10, 5))

        ttk.Label(frame_account, text="账号:").grid(row=0, column=0, sticky="w")
        self.entry_username = ttk.Entry(frame_account, width=30)
        self.entry_username.grid(row=0, column=1, padx=5, pady=3)

        ttk.Label(frame_account, text="密码:").grid(row=1, column=0, sticky="w")
        self.entry_password = ttk.Entry(frame_account, width=30, show="*")
        self.entry_password.grid(row=1, column=1, padx=5, pady=3)

        # 设置区
        frame_settings = ttk.LabelFrame(self.root, text="保活设置", padding=10)
        frame_settings.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame_settings, text="检测间隔(秒):").grid(row=0, column=0, sticky="w")
        self.entry_interval = ttk.Entry(frame_settings, width=10)
        self.entry_interval.grid(row=0, column=1, sticky="w", padx=5, pady=3)

        # 控制按钮
        frame_btn = ttk.Frame(self.root, padding=10)
        frame_btn.pack(fill="x", padx=10)

        self.btn_start = ttk.Button(frame_btn, text="▶ 开始保活", command=self.start)
        self.btn_start.pack(side="left", padx=5)

        self.btn_stop = ttk.Button(frame_btn, text="■ 停止", command=self.stop, state="disabled")
        self.btn_stop.pack(side="left", padx=5)

        self.btn_save = ttk.Button(frame_btn, text="💾 保存配置", command=self.save)
        self.btn_save.pack(side="right", padx=5)

        # 状态区
        frame_status = ttk.LabelFrame(self.root, text="运行状态", padding=10)
        frame_status.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        self.label_status = ttk.Label(frame_status, text="● 未运行", foreground="gray")
        self.label_status.pack(anchor="w")

        self.label_online = ttk.Label(frame_status, text="网络状态: 未知")
        self.label_online.pack(anchor="w", pady=(5, 0))

        self.label_last_check = ttk.Label(frame_status, text="上次检测: -")
        self.label_last_check.pack(anchor="w")

        self.label_reconnect = ttk.Label(frame_status, text="重连次数: 0")
        self.label_reconnect.pack(anchor="w")

        # 日志区
        self.text_log = tk.Text(frame_status, height=6, font=("Consolas", 9))
        self.text_log.pack(fill="both", expand=True, pady=(5, 0))
        self.text_log.config(state="disabled")

        self.reconnect_count = 0

    def load_ui_from_config(self):
        self.entry_username.insert(0, self.config.get("username", ""))
        self.entry_password.insert(0, self.config.get("password", ""))
        self.entry_interval.insert(0, str(self.config.get("interval", 60)))

    def log(self, msg):
        now = datetime.now().strftime("%H:%M:%S")
        self.text_log.config(state="normal")
        self.text_log.insert("end", f"[{now}] {msg}\n")
        self.text_log.see("end")
        self.text_log.config(state="disabled")

    def save(self):
        config = {
            "username": self.entry_username.get(),
            "password": self.entry_password.get(),
            "interval": int(self.entry_interval.get() or 60)
        }
        save_config(config)
        self.log("配置已保存")

    def start(self):
        username = self.entry_username.get().strip()
        password = self.entry_password.get().strip()
        if not username or not password:
            messagebox.showwarning("提示", "请先填写账号和密码")
            return

        self.save()
        self.running = True
        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")
        self.label_status.config(text="● 运行中", foreground="green")
        self.log("保活已启动")

        self.thread = threading.Thread(target=self.keep_alive_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        self.btn_start.config(state="normal")
        self.btn_stop.config(state="disabled")
        self.label_status.config(text="● 已停止", foreground="gray")
        self.log("保活已停止")

    def minimize_to_tray(self):
        """最小化到系统托盘"""
        self.root.withdraw()  # 隐藏窗口

        menu = pystray.Menu(
            pystray.MenuItem("显示窗口", self.restore_from_tray),
            pystray.MenuItem("退出", self.quit_app)
        )

        self.tray_icon = pystray.Icon(
            "CUG校园网保活",
            create_tray_icon(),
            "CUG校园网保活 - 运行中",
            menu
        )

        # 在新线程中运行托盘图标
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def restore_from_tray(self, icon=None, item=None):
        """从托盘恢复窗口"""
        if self.tray_icon:
            self.tray_icon.stop()
            self.tray_icon = None
        self.root.after(0, self.root.deiconify)

    def quit_app(self, icon=None, item=None):
        """完全退出程序"""
        self.running = False
        if self.tray_icon:
            self.tray_icon.stop()
            self.tray_icon = None
        self.root.after(0, self.root.destroy)

    def keep_alive_loop(self):
        while self.running:
            try:
                online = is_online()
                now = datetime.now().strftime("%H:%M:%S")

                self.root.after(0, self.label_last_check.config, {"text": f"上次检测: {now}"})

                if online:
                    self.root.after(0, self.label_online.config,
                                    {"text": "网络状态: ✓ 在线", "foreground": "green"})
                    self.root.after(0, self.log, "网络正常")
                else:
                    self.root.after(0, self.label_online.config,
                                    {"text": "网络状态: × 掉线", "foreground": "red"})
                    self.root.after(0, self.log, "检测到掉线，正在重连...")

                    username = self.entry_username.get()
                    password = self.entry_password.get()

                    success, err = reconnect(username, password)
                    if success:
                        self.reconnect_count += 1
                        self.root.after(0, self.label_reconnect.config,
                                        {"text": f"重连次数: {self.reconnect_count}"})
                        self.root.after(0, self.label_online.config,
                                        {"text": "网络状态: ✓ 已重连", "foreground": "green"})
                        self.root.after(0, self.log, "重连成功！")
                    else:
                        self.root.after(0, self.log, f"重连失败: {err[:50]}")

            except Exception as e:
                self.root.after(0, self.log, f"异常: {str(e)[:50]}")

            # 按间隔等待，每秒检查一次是否被停止
            interval = int(self.entry_interval.get() or 60)
            for _ in range(interval):
                if not self.running:
                    break
                time.sleep(1)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = KeepAliveApp()
    app.run()

