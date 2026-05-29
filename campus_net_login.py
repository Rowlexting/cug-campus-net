import requests
import subprocess
import time
import sys
import io

# 修复终端编码问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ========= 配置区 =========
LOGIN_URL = "http://192.168.167.115/"
USERNAME = "your_student_id"
PASSWORD = "your_password"
HEADLESS = False       # True=后台静默运行，False=显示浏览器窗口（调试用）
WIFI_TIMEOUT = 60      # 等待WiFi连接的最大时间（秒）
# =========================


def wait_for_wifi():
    """等待电脑连上WiFi，最多等待 WIFI_TIMEOUT 秒"""
    for i in range(WIFI_TIMEOUT):
        # 尝试多种编码读取
        result = subprocess.run(
            ["netsh", "wlan", "show", "interfaces"],
            capture_output=True
        )
        raw = result.stdout
        # 尝试 utf-8 和 gbk 两种解码
        for enc in ["utf-8", "gbk", "cp437"]:
            try:
                stdout = raw.decode(enc, errors="ignore")
                if "已连接" in stdout or "connected" in stdout.lower():
                    return True
            except Exception:
                continue
        # 调试输出
        if i == 0:
            print(f"  [调试] 原始字节前100: {raw[:100]}")
            try:
                print(f"  [调试] utf-8解码: {raw.decode('utf-8', errors='replace')[:200]}")
            except:
                pass
        if i % 5 == 0:
            print(f"  等待WiFi连接中... ({i}/{WIFI_TIMEOUT}s)")
        time.sleep(1)
    return False


def is_already_online():
    """检测是否已经登录校园网：尝试访问外网，能通就是已登录"""
    try:
        resp = requests.get("http://www.baidu.com", timeout=5)
        # 如果能正常访问百度，且没有被重定向到校园网认证页面
        if resp.status_code == 200 and "192.168.167.115" not in resp.url and "nap.cug.edu.cn" not in resp.url:
            return True
    except requests.RequestException:
        pass
    return False


def login_campus_net():
    """使用 Selenium 登录校园网"""
    options = Options()
    if HEADLESS:
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--log-level=3")

    driver = webdriver.Chrome(options=options)
    try:
        driver.get(LOGIN_URL)

        # 等待账号输入框出现（最多 15 秒）
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//input[@placeholder='请输入账号']"))
        )

        driver.find_element(By.XPATH, "//input[@placeholder='请输入账号']").send_keys(USERNAME)
        driver.find_element(By.XPATH, "//input[@placeholder='请输入密码']").send_keys(PASSWORD)
        driver.find_element(By.XPATH, "//button[contains(text(),'登录')]").click()

        # 等待页面跳转到成功页面
        WebDriverWait(driver, 10).until(
            lambda d: "success" in d.page_source or "已用流量" in d.page_source
        )
        return True
    except Exception as e:
        print(f"  登录操作失败: {e}")
        return False
    finally:
        driver.quit()


def main():
    print("=" * 40)
    print("  校园网自动登录脚本")
    print("=" * 40)

    # 等待WiFi连接
    print("\n[1/3] 检测WiFi连接...")
    if wait_for_wifi():
        print("  ✓ 检测到已经连上WiFi")
    else:
        print("  × WiFi未连接，脚本退出")
        sys.exit(1)

    # 检测是否已经在线
    print("\n[2/3] 检测网络状态...")
    if is_already_online():
        print("  ✓ 已经登录校园网，无需重复登录")
        return

    # 未登录，执行登录
    print("  × 未登录，准备自动登录...")
    print("\n[3/3] 正在登录...")

    if login_campus_net():
        print("\n  ✓ 校园网登录成功！")
    else:
        print("\n  × 登录失败，请检查网络连接或手动登录")
        sys.exit(1)


if __name__ == "__main__":
    main()
