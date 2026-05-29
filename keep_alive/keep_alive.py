import requests
import subprocess
import sys
import os

# ========= 配置区 =========
LOGIN_URL = "http://192.168.167.115/"
USERNAME = "your_student_id"
PASSWORD = "your_password"
HEADLESS = False       # True=后台静默运行，False=显示浏览器窗口（调试用）
# =========================

# 获取登录脚本所在目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)


def is_online():
    """检测是否在线"""
    try:
        resp = requests.get("http://www.baidu.com", timeout=5)
        if resp.status_code == 200 and "192.168.167.115" not in resp.url and "nap.cug.edu.cn" not in resp.url:
            return True
    except requests.RequestException:
        pass
    return False


def reconnect():
    """调用登录脚本重新连接"""
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    options = Options()
    if HEADLESS:
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--log-level=3")

    driver = webdriver.Chrome(options=options)
    try:
        driver.get(LOGIN_URL)

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//input[@placeholder='请输入账号']"))
        )

        driver.find_element(By.XPATH, "//input[@placeholder='请输入账号']").send_keys(USERNAME)
        driver.find_element(By.XPATH, "//input[@placeholder='请输入密码']").send_keys(PASSWORD)
        driver.find_element(By.XPATH, "//button[contains(text(),'登录')]").click()

        WebDriverWait(driver, 10).until(
            lambda d: "success" in d.page_source or "已用流量" in d.page_source
        )
        return True
    except Exception as e:
        print(f"  重连失败: {e}")
        return False
    finally:
        driver.quit()


def main():
    if is_online():
        print("[保活] ✓ 网络正常")
    else:
        print("[保活] × 检测到掉线，正在重连...")
        if reconnect():
            print("[保活] ✓ 重连成功！")
        else:
            print("[保活] × 重连失败")
            sys.exit(1)


if __name__ == "__main__":
    main()
