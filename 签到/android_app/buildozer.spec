[app]
title = 心遇助手
package.name = moyihelper
package.domain = org.moyi
source.dir = .
source.main = main.py
source.include_exts = py,png,jpg,kv,atlas,json,ttf,otc,ttc
version = 1.0.0
requirements = python3==3.11.6,kivy==2.3.0,requests,urllib3,certifi,charset-normalizer,idna
orientation = portrait
fullscreen = 0
android.bootstrap = sdl2
android.permissions = INTERNET
android.api = 33
android.minapi = 21
android.archs = arm64-v8a
android.accept_sdk_license = True
android.allow_backup = True
android.debuggable = 1
p4a.branch = stable
android.ndk = 25b

[buildozer]
log_level = 2
warn_on_root = 0
