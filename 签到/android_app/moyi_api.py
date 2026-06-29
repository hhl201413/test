"""心遇 API 逻辑（桌面版与 Android 版共用）"""
import json
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


def sign_in_xiangfeng(acc, log_callback):
    nickname = acc.get('nickname', '未知')
    cookie_str = acc.get('cookie', '')
    try:
        log_callback(f"[{nickname}] 开始相逢有礼...")
        cookies = parse_cookie(cookie_str)
        headers = get_api_headers('WebViewActivity')
        data = 'Q1NKTWS8DADro1WsXN+j0URXuX0Qf3k1ia2gknRAcucG9+5NQUoAAAA8BKMUbNSzDq97DLuUAY07gH2HbNS6LndiCJvHpAevdAbTBMIOZiYmstPfF7M9NE8JgdWVK3uJlctuco69+xTth561F842IQO9Ig=='
        response = requests.post(
            'https://api.moyi.163.com/neapi/moyi/activity/common/key/storage',
            cookies=cookies, headers=headers, data=data, timeout=10
        )
        log_callback(f"[{nickname}] 状态码: {response.status_code}")
        log_callback(f"[{nickname}] 返回: {response.text}")
        return True, "成功"
    except Exception as e:
        log_callback(f"[{nickname}] 失败: {str(e)}")
        return False, str(e)


def send_gift_single(acc, gift_config, log_callback):
    nickname = acc.get('nickname', '未知')
    cookie_str = acc.get('cookie', '')
    try:
        log_callback(f"[{nickname}] 开始送礼物...")
        cookies = parse_cookie(cookie_str)
        headers = get_api_headers('WebViewActivity')
        receiver_ids = [rid.strip() for rid in gift_config['receiverIds'].split(',') if rid.strip()]
        if not receiver_ids:
            log_callback(f"[{nickname}] 失败: 接收者ID不能为空")
            return False, "接收者ID不能为空"
        ext = gift_config.get('ext') or '{"auctionId":-1,"fastPanel":false,"fastPanelSource":"","played":1}'
        json.loads(ext)
        data = {
            'resourceId': gift_config['resourceId'],
            'resourceType': gift_config['resourceType'],
            'scene': gift_config['scene'],
            'sceneId': gift_config['sceneId'],
            'num': gift_config['num'],
            'ext': ext,
            'receiverIds': json.dumps(receiver_ids, separators=(',', ':')),
        }
        response = requests.post(
            'https://api.moyi.163.com/api/moyi/packresource/present',
            cookies=cookies, headers=headers, data=data, timeout=10
        )
        log_callback(f"[{nickname}] 状态码: {response.status_code}")
        log_callback(f"[{nickname}] 返回: {response.text}")
        return True, "成功"
    except json.JSONDecodeError:
        log_callback(f"[{nickname}] 失败: ext 不是合法 JSON")
        return False, "ext 不是合法 JSON"
    except Exception as e:
        log_callback(f"[{nickname}] 失败: {str(e)}")
        return False, str(e)
