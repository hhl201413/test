import json
import os
import sys
import threading
import time

# 必须在创建界面控件前注册中文字体，否则中文显示为方框/乱码
from kivy.config import Config
from kivy.core.text import LabelBase

CN_FONT = 'CnFont'


def _find_chinese_font():
  app_dir = os.path.dirname(os.path.abspath(__file__))
  bundled = [
    os.path.join(app_dir, 'fonts', 'noto.ttc'),
    os.path.join(app_dir, 'fonts', 'msyh.ttc'),
    os.path.join(app_dir, 'fonts', 'simhei.ttf'),
    os.path.join(app_dir, 'fonts', 'NotoSansSC-Regular.otf'),
  ]
  windir = os.environ.get('WINDIR', r'C:\Windows')
  fonts_dir = os.path.join(windir, 'Fonts')
  candidates = bundled + [
    os.path.join(fonts_dir, 'msyh.ttc'),
    os.path.join(fonts_dir, 'msyhbd.ttc'),
    os.path.join(fonts_dir, 'simhei.ttf'),
    os.path.join(fonts_dir, 'simsun.ttc'),
    '/system/fonts/NotoSansCJK-Regular.ttc',
    '/system/fonts/DroidSansFallback.ttf',
  ]
  for path in candidates:
    if os.path.isfile(path):
      return path
  return None


def setup_chinese_font():
  path = _find_chinese_font()
  if not path:
    return None
  try:
    LabelBase.register(name=CN_FONT, fn_regular=path)
    Config.set('kivy', 'default_font', [CN_FONT, 'Roboto', 'Helvetica', 'Arial'])
    return CN_FONT
  except Exception as e:
    print(f'注册中文字体失败: {e}', file=sys.stderr)
    return None


FONT_NAME = setup_chinese_font()

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

import moyi_api


def _font_kwargs(font_name):
  return {'font_name': font_name} if font_name else {}


class MoyiApp(App):
  title = '心遇助手'

  def build(self):
    self.font_name = FONT_NAME
    self.fk = _font_kwargs(self.font_name)
    self.accounts = []
    self.data_dir = self.user_data_dir
    self.accounts_file = os.path.join(self.data_dir, 'accounts.json')
    self._load_accounts()

    root = BoxLayout(orientation='vertical', padding=8, spacing=8)

    toolbar = BoxLayout(size_hint_y=None, height=44, spacing=6)
    toolbar.add_widget(Button(text='添加账号', on_press=self._show_add_account, **self.fk))
    toolbar.add_widget(Button(text='一键签到', on_press=self._batch_sign_in, **self.fk))
    root.add_widget(toolbar)

    self.account_label = Label(
      text=self._account_summary(),
      size_hint_y=None,
      height=30,
      color=(0.2, 0.2, 0.2, 1),
      **self.fk,
    )
    root.add_widget(self.account_label)

    self.log_view = TextInput(readonly=True, font_size=13, **self.fk)
    scroll = ScrollView()
    scroll.add_widget(self.log_view)
    root.add_widget(scroll)

    if self.font_name:
      self._log('心遇助手已启动')
    else:
      self._log('未找到系统中文字体，中文可能显示异常')
    return root

  def _account_summary(self):
    return f'共 {len(self.accounts)} 个账号'

  def _load_accounts(self):
    os.makedirs(self.data_dir, exist_ok=True)
    if os.path.exists(self.accounts_file):
      try:
        with open(self.accounts_file, 'r', encoding='utf-8') as f:
          self.accounts = json.load(f)
      except Exception:
        self.accounts = []

  def _save_accounts(self):
    with open(self.accounts_file, 'w', encoding='utf-8') as f:
      json.dump(self.accounts, f, ensure_ascii=False, indent=2)
    Clock.schedule_once(lambda *_: setattr(
      self.account_label, 'text', self._account_summary()
    ))

  def _log(self, msg):
    def append(_dt):
      self.log_view.text += msg + '\n'
      self.log_view.cursor = (0, len(self.log_view.text))
    Clock.schedule_once(append)

  def _show_add_account(self, *_):
    box = BoxLayout(orientation='vertical', padding=10, spacing=8)
    nick = TextInput(hint_text='昵称', multiline=False, **self.fk)
    cookie = TextInput(hint_text='Cookie', multiline=True, size_hint_y=None, height=120, **self.fk)
    remark = TextInput(hint_text='备注', multiline=False, **self.fk)
    box.add_widget(nick)
    box.add_widget(cookie)
    box.add_widget(remark)

    popup_kw = {'title': '添加账号', 'content': box, 'size_hint': (0.92, 0.7)}
    if self.font_name:
      popup_kw['title_font'] = self.font_name
    popup = Popup(**popup_kw)

    def save(_):
      n, c = nick.text.strip(), cookie.text.strip()
      if not n or not c:
        self._log('添加失败：昵称和 Cookie 不能为空')
        return
      self.accounts.append({'nickname': n, 'cookie': c, 'remark': remark.text.strip()})
      self._save_accounts()
      self._log(f'已添加账号: {n}')
      popup.dismiss()

    actions = BoxLayout(size_hint_y=None, height=44, spacing=8)
    actions.add_widget(Button(text='保存', on_press=save, **self.fk))
    actions.add_widget(Button(text='取消', on_press=lambda *_: popup.dismiss(), **self.fk))
    box.add_widget(actions)
    popup.open()

  def _run_batch(self, title, worker):
    if not self.accounts:
      self._log('无账号')
      return
    self._log(f'===== {title} 开始 =====')

    def run():
      worker()
      Clock.schedule_once(lambda *_: self._log(f'===== {title} 完成 ====='))

    threading.Thread(target=run, daemon=True).start()

  def _batch_sign_in(self, *_):
    def worker():
      for acc in self.accounts:
        moyi_api.sign_in_single(acc, self._log)
        time.sleep(2)
    self._run_batch('签到', worker)


if __name__ == '__main__':
  MoyiApp().run()
