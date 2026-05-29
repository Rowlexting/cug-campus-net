# CUG Campus Net

中国地质大学（武汉）校园网自动登录 & 保活工具。

基于深澜（Srun）认证协议，支持开机自动连接校园网、定时检测掉线并自动重连。

## 功能

- **开机自动登录**：电脑启动后自动连接校园网（关闭代理、杀掉 Clash、等待 WiFi、自动登录）
- **保活检测**：定时检测网络状态，掉线自动重连（防止被其他设备挤掉）
- **GUI 工具**：带图形界面的保活程序，支持系统托盘最小化，可打包为 exe 分发给同学

## 项目结构

```
campus_net/
├── campus_net_login.py          # 开机自动登录脚本（Selenium 版）
├── keep_alive/
│   ├── srun_login.py            # 深澜协议纯 requests 登录（核心）
│   ├── keep_alive.py            # 命令行保活脚本
│   ├── keep_alive_gui.py        # GUI 保活程序（tkinter）
│   ├── keep_alive.bat           # 命令行保活启动器
│   └── uninstall.py             # 卸载程序
└── .gitignore
```

## 快速开始

### 方式一：GUI 工具（推荐给普通用户）

下载 Release 中的 `CUG校园网保活.exe`，双击运行，填入学号和密码，点击"开始保活"即可。

### 方式二：命令行使用

1. 安装依赖：

```bash
pip install requests selenium
```

2. 修改 `campus_net_login.py` 中的账号密码：

```python
USERNAME = "你的学号"
PASSWORD = "你的密码"
```

3. 运行：

```bash
python campus_net_login.py
```

### 方式三：开机自启动

将 `campus_net_autostart.bat` 放入 Windows 启动文件夹：

```
C:\Users\<用户名>\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\
```

## 纯 requests 登录（无需浏览器）

`keep_alive/srun_login.py` 实现了深澜认证协议的完整流程，不依赖 Selenium 和 Chrome：

```python
from srun_login import srun_login

success, msg = srun_login("学号", "密码")
print(msg)
```

## 打包为 exe

```bash
pip install pyinstaller pillow pystray
cd keep_alive
pyinstaller --onefile --windowed --name "CUG校园网保活" --hidden-import srun_login keep_alive_gui.py
```

生成的 exe 在 `dist/` 目录下，可直接分发，无需安装任何环境。

## 适用范围

- 中国地质大学（武汉）校园网（深澜/Srun 认证系统）
- 其他使用深澜认证系统的高校，修改 `LOGIN_URL` 即可适配

## License

MIT
