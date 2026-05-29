import os
import sys
import subprocess
import shutil

def main():
    print("=" * 40)
    print("  CUG校园网保活 - 卸载程序")
    print("=" * 40)

    # 获取当前目录
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    print("\n将执行以下操作：")
    print("  1. 删除 Windows 定时任务 (CampusNetKeepAlive)")
    print("  2. 删除配置文件 (config.json)")
    print("  3. 删除程序文件")

    choice = input("\n确认卸载？(y/n): ").strip().lower()
    if choice != 'y':
        print("已取消")
        input("按回车退出...")
        return

    # 1. 删除定时任务
    print("\n[1/3] 删除定时任务...")
    result = subprocess.run(
        ["schtasks", "/Delete", "/TN", "CampusNetKeepAlive", "/F"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print("  ✓ 定时任务已删除")
    else:
        print("  - 未找到定时任务（可能未创建过）")

    # 2. 删除配置文件
    print("[2/3] 删除配置文件...")
    config_path = os.path.join(base_dir, "config.json")
    if os.path.exists(config_path):
        os.remove(config_path)
        print("  ✓ config.json 已删除")
    else:
        print("  - 未找到配置文件")

    # 3. 删除程序文件（延迟自删除）
    print("[3/3] 删除程序文件...")
    exe_path = os.path.join(base_dir, "CUG校园网保活.exe")
    uninstall_path = sys.executable if getattr(sys, 'frozen', False) else __file__

    print("\n  ✓ 卸载完成！")
    print("  程序文件将在关闭后自动删除。")
    input("\n按回车退出...")

    # 用 cmd 延迟删除自身和主程序
    if getattr(sys, 'frozen', False):
        # 删除 exe 自身和主程序
        bat_content = f'''@echo off
timeout /t 2 /nobreak >nul
del /f /q "{exe_path}" 2>nul
del /f /q "{uninstall_path}" 2>nul
del /f /q "%~f0"
'''
        bat_path = os.path.join(base_dir, "_cleanup.bat")
        with open(bat_path, "w") as f:
            f.write(bat_content)
        subprocess.Popen(
            ["cmd", "/c", bat_path],
            creationflags=subprocess.CREATE_NO_WINDOW
        )


if __name__ == "__main__":
    main()
