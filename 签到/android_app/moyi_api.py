"""心遇 API 逻辑（桌面版与 Android 版共用）"""
import json
import os

try:
    import certifi
    os.environ.setdefault('REQUESTS_CA_BUNDLE', certifi.where())
    os.environ.setdefault('SSL_CERT_FILE', certifi.where())
except ImportError:
    pass

import requests


def parse_cookie(s):
    d = {}
    for i in s.split(';'):
        i = i.strip()
        if '=' in i:
            k, v = i.split('=', 1)
            d[k.strip()] = v.strip()
    return d


def get_api_headers(cm_page_id='WebViewActivity'):
    return {
        'cm_no_encrypt_native_tag_20220105': 'false',
        'CMPageId': cm_page_id,
        'User-Agent': 'NeteaseMoyi/2.20.0.260305100204(195);Dalvik/2.1.0 (Linux; U; Android 16; PLQ110 Build/BP2A.250605.015)',
        'X-ER': '25788',
        'MConfig-Info': '{"TT5Fdk0jbjHC6OZ5":{"version":"9361408","appver":"2.20.0"}}',
        'X-MAM-CustomMark': 'okhttp',
        'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8',
    }


def sign_in_single(acc, log_callback):
    nickname = acc.get('nickname', '未知')
    cookie_str = acc.get('cookie', '')
    try:
        log_callback(f"[{nickname}] 开始签到...")
        cookies = parse_cookie(cookie_str)
        headers = get_api_headers('moyi_signin@index')
        data = 'Q1NKTWS8DABiQV9NbCRvXHv8HEwQlWl5MGQ0jZmsNbUgLQ4z6BoAAACSo7weP6yqBIwMIsn0jVtAzgI/DPzoWffYLg=='
        response = requests.post(
            'https://api.moyi.163.com/neapi/moyi/user/sign/in',
            cookies=cookies, headers=headers, data=data, timeout=10
        )
        log_callback(f"[{nickname}] 状态码: {response.status_code}")
        log_callback(f"[{nickname}] 返回: {response.text}")
        return True, "成功"
    except Exception as e:
        log_callback(f"[{nickname}] 失败: {str(e)}")
        return False, str(e)
