[app]
title = 心遇助手
package.name = moyihelper
package.domain = org.moyi
source.dir = .
source.main = main.py
source.include_exts = py,png,jpg,kv,atlas,json,ttf,otc,ttc
version = 1.0.0
requirements = python3,kivy,requests,urllib3,certifi,charset-normalizer,idna,android
orientation = portrait
fullscreen = 0
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 31
android.minapi = 21
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True
android.allow_backup = True
android.debuggable = 1

[buildozer]
log_level = 2
warn_on_root = 1
