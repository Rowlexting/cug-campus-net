"""
CUG 校园网登录 - 纯 requests 方案（无需浏览器）
基于深澜(Srun)认证协议
"""
import requests
import hashlib
import hmac
import json
import re
import math
import time


# ========= 加密算法 =========

def md5_hash(password, token):
    """HMAC-MD5 加密密码"""
    return hmac.HMAC(token.encode(), password.encode(), hashlib.md5).hexdigest()


def sha1_hash(value):
    """SHA1 哈希"""
    return hashlib.sha1(value.encode()).hexdigest()


def xxtea_encode(str_data, key):
    """XXTEA 加密"""
    if str_data == '':
        return ''

    v = _str2long(str_data, True)
    k = _str2long(key, False)

    if len(k) < 4:
        k = k + [0] * (4 - len(k))

    n = len(v) - 1
    z = v[n]
    y = v[0]
    c = 0x9E3779B9
    q = 6 + 52 // (n + 1)
    d = 0

    while q > 0:
        d = (d + c) & 0xFFFFFFFF
        e = (d >> 2) & 3
        for p in range(n):
            y = v[p + 1]
            m = ((z >> 5) ^ (y << 2)) & 0xFFFFFFFF
            m = (m + (((y >> 3) ^ (z << 4)) ^ (d ^ y))) & 0xFFFFFFFF
            m = (m + (k[(p & 3) ^ e] ^ z)) & 0xFFFFFFFF
            z = v[p] = (v[p] + m) & 0xFFFFFFFF
        y = v[0]
        m = ((z >> 5) ^ (y << 2)) & 0xFFFFFFFF
        m = (m + (((y >> 3) ^ (z << 4)) ^ (d ^ y))) & 0xFFFFFFFF
        m = (m + (k[(n & 3) ^ e] ^ z)) & 0xFFFFFFFF
        z = v[n] = (v[n] + m) & 0xFFFFFFFF
        q -= 1

    return _long2str(v, False)


def _str2long(s, include_length):
    """字符串转长整型数组"""
    length = len(s)
    v = []
    for i in range(0, length, 4):
        v.append(
            ord(s[i]) |
            (ord(s[i + 1]) << 8 if i + 1 < length else 0) |
            (ord(s[i + 2]) << 16 if i + 2 < length else 0) |
            (ord(s[i + 3]) << 24 if i + 3 < length else 0)
        )
    if include_length:
        v.append(length)
    return v


def _long2str(v, include_length):
    """长整型数组转字符串"""
    n = len(v)
    if include_length:
        m = v[n - 1]
        c = (n - 1) << 2
        if m < c - 3 or m > c:
            return None
        c = m
    else:
        c = n << 2

    result = []
    for i in range(n):
        result.append(chr(v[i] & 0xFF))
        result.append(chr((v[i] >> 8) & 0xFF))
        result.append(chr((v[i] >> 16) & 0xFF))
        result.append(chr((v[i] >> 24) & 0xFF))

    if include_length:
        return ''.join(result)[:c]
    else:
        return ''.join(result)


# 自定义 Base64 编码
_ALPHA = 'LVoJPiCN2R8G90yg+hmFHuacZ1OWMnrsSTXkYpUq/3dlbfKwv6xztjI7DeBE45QA'
_PAD = '='


def custom_base64_encode(s):
    """使用深澜自定义字母表的 Base64 编码"""
    result = []
    length = len(s)
    i = 0
    while i < length:
        b0 = ord(s[i]) if i < length else 0
        b1 = ord(s[i + 1]) if i + 1 < length else 0
        b2 = ord(s[i + 2]) if i + 2 < length else 0

        result.append(_ALPHA[(b0 >> 2) & 0x3F])
        result.append(_ALPHA[((b0 << 4) | (b1 >> 4)) & 0x3F])

        if i + 1 < length:
            result.append(_ALPHA[((b1 << 2) | (b2 >> 6)) & 0x3F])
        else:
            result.append(_PAD)

        if i + 2 < length:
            result.append(_ALPHA[b2 & 0x3F])
        else:
            result.append(_PAD)

        i += 3

    return ''.join(result)


def encode_user_info(info, token):
    """加密用户信息"""
    info_json = json.dumps(info, separators=(',', ':'))
    encoded = xxtea_encode(info_json, token)
    return '{SRBX1}' + custom_base64_encode(encoded)


# ========= 登录逻辑 =========

class SrunLogin:
    def __init__(self, server="http://192.168.167.115", username="", password=""):
        self.server = server.rstrip('/')
        self.username = username
        self.password = password
        self.ac_id = 1
        self.n = 200
        self.type = 1
        self.enc = 'srun_bx1'
        self.ip = ''
        self.token = ''
        self.session = requests.Session()

    def get_ip(self):
        """获取本机在校园网中的 IP"""
        try:
            # 直接访问认证页面获取 IP
            resp = self.session.get(
                f"{self.server}/srun_portal_pc?ac_id={self.ac_id}&theme=pro",
                timeout=5
            )
            match = re.search(r'ip\s*:\s*"([^"]+)"', resp.text)
            if match:
                self.ip = match.group(1)
                return True
        except Exception:
            pass
        return False

    def get_token(self):
        """获取认证 token (challenge)"""
        params = {
            'callback': 'srun_callback',
            'username': self.username,
            'ip': self.ip,
        }
        try:
            resp = self.session.get(
                f"{self.server}/cgi-bin/get_challenge",
                params=params, timeout=5
            )
            # 解析 JSONP 响应
            match = re.search(r'srun_callback\((.+)\)', resp.text)
            if match:
                data = json.loads(match.group(1))
                if 'challenge' in data:
                    self.token = data['challenge']
                    return True
        except Exception:
            pass
        return False

    def login(self):
        """执行登录"""
        if not self.get_ip():
            return False, "无法获取 IP 地址"

        if not self.get_token():
            return False, "无法获取 token"

        # MD5 加密密码
        hmd5 = hmac.HMAC(
            self.token.encode(), self.password.encode(), hashlib.md5
        ).hexdigest()

        # 加密用户信息
        info = encode_user_info({
            'username': self.username,
            'password': self.password,
            'ip': self.ip,
            'acid': str(self.ac_id),
            'enc_ver': self.enc
        }, self.token)

        # 计算校验和
        chksum_str = self.token + self.username
        chksum_str += self.token + hmd5
        chksum_str += self.token + str(self.ac_id)
        chksum_str += self.token + self.ip
        chksum_str += self.token + str(self.n)
        chksum_str += self.token + str(self.type)
        chksum_str += self.token + info
        chksum = sha1_hash(chksum_str)

        # 发起认证请求
        params = {
            'callback': 'srun_callback',
            'action': 'login',
            'username': self.username,
            'password': '{MD5}' + hmd5,
            'ac_id': str(self.ac_id),
            'ip': self.ip,
            'info': info,
            'chksum': chksum,
            'n': str(self.n),
            'type': str(self.type),
        }

        try:
            resp = self.session.get(
                f"{self.server}/cgi-bin/srun_portal",
                params=params, timeout=10
            )
            match = re.search(r'srun_callback\((.+)\)', resp.text)
            if match:
                data = json.loads(match.group(1))
                if data.get('error') == 'ok':
                    return True, f"登录成功 (IP: {self.ip})"
                else:
                    return False, data.get('error_msg', data.get('error', '未知错误'))
        except Exception as e:
            return False, str(e)

        return False, "请求失败"


def srun_login(username, password, server="http://192.168.167.115"):
    """便捷登录函数"""
    client = SrunLogin(server=server, username=username, password=password)
    return client.login()


if __name__ == "__main__":
    # 测试
    success, msg = srun_login("your_student_id", "your_password")
    print(f"结果: {msg}")

