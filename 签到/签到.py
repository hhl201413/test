import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import json
import os
import sys
import time
import threading
import schedule
from datetime import datetime, timedelta
import random


def _init_ssl_certs():
    """PyInstaller 打包后 requests 找不到 cacert.pem，需手动指定证书路径"""
    if not getattr(sys, 'frozen', False):
        return
    base = getattr(sys, '_MEIPASS', '')
    candidates = [
        os.path.join(base, 'certifi', 'cacert.pem'),
        os.path.join(base, 'requests', 'cacert.pem'),
    ]
    try:
        import certifi
        candidates.insert(0, certifi.where())
    except ImportError:
        pass
    for path in candidates:
        if path and os.path.isfile(path):
            os.environ['REQUESTS_CA_BUNDLE'] = path
            os.environ['SSL_CERT_FILE'] = path
            break


_init_ssl_certs()
import requests

BASE_DIR = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')


def _migrate_data_files():
    os.makedirs(DATA_DIR, exist_ok=True)
    for name in ('accounts.json', 'schedule_config.json'):
        old = os.path.join(BASE_DIR, name)
        new = os.path.join(DATA_DIR, name)
        if os.path.exists(old) and not os.path.exists(new):
            try:
                os.replace(old, new)
            except OSError:
                pass


_migrate_data_files()


class AccountDialog(tk.Toplevel):
    """账号添加/编辑对话框"""
    def __init__(self, parent, title, account=None):
        super().__init__(parent)
        self.title(title)
        self.geometry("550x350")
        self.transient(parent)
        self.grab_set()
        self.result = None

        self.account = account or {'nickname': '', 'cookie': '', 'remark': ''}

        frame = tk.Frame(self, padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text="昵称（必填）", font=('Arial', 10)).pack(anchor='w')
        self.nickname_var = tk.StringVar(value=self.account['nickname'])
        tk.Entry(frame, textvariable=self.nickname_var, font=('Arial', 10)).pack(fill=tk.X, pady=5)

        tk.Label(frame, text="Cookie（必填）", font=('Arial', 10)).pack(anchor='w')
        self.cookie_var = tk.StringVar(value=self.account['cookie'])
        tk.Entry(frame, textvariable=self.cookie_var, font=('Arial', 10)).pack(fill=tk.X, pady=5)

        tk.Label(frame, text="备注", font=('Arial', 10)).pack(anchor='w')
        self.remark_var = tk.StringVar(value=self.account['remark'])
        tk.Entry(frame, textvariable=self.remark_var, font=('Arial', 10)).pack(fill=tk.X, pady=5)

        btn_frame = tk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=20)

        tk.Button(btn_frame, text="保存", command=self.save, bg='#4CAF50', fg='white',
                  font=('Arial', 10, 'bold'), width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="取消", command=self.destroy, bg='#f44336', fg='white',
                  font=('Arial', 10, 'bold'), width=10).pack(side=tk.RIGHT, padx=5)

    def save(self):
        nickname = self.nickname_var.get().strip()
        cookie = self.cookie_var.get().strip()
        remark = self.remark_var.get().strip()

        if not nickname:
            messagebox.showerror("错误", "昵称不能为空！")
            return
        if not cookie:
            messagebox.showerror("错误", "Cookie不能为空！")
            return

        self.result = {
            'nickname': nickname,
            'cookie': cookie,
            'remark': remark
        }
        messagebox.showinfo("成功", "账号已保存！")
        self.destroy()


class AccountManager:
    def __init__(self, root):
        self.root = root
        self.root.title("账号管理系统")
        self.root.geometry("1200x600")

        self.data_file = os.path.join(DATA_DIR, 'accounts.json')
        self.schedule_file = os.path.join(DATA_DIR, 'schedule_config.json')
        self.accounts = []

        self.scheduler_running = False
        self.scheduler_thread = None
        self.schedule_config = self.load_schedule_config()
        self.next_run_time = None

        self.load_accounts()
        self.create_widgets()
        self.refresh_table()

        if self.schedule_config.get('enabled'):
            self.apply_schedule()
            self.start_scheduler()

    def _parse_time_parts(self, time_str):
        parts = time_str.strip().split(':')
        return int(parts[0]), int(parts[1])

    def _random_time_in_range(self):
        sh, sm = self._parse_time_parts(self.schedule_config['start_time'])
        eh, em = self._parse_time_parts(self.schedule_config['end_time'])
        start_m = sh * 60 + sm
        end_m = eh * 60 + em
        if end_m < start_m:
            end_m = start_m
        pick = random.randint(start_m, end_m)
        return pick // 60, pick % 60

    def apply_schedule(self):
        schedule.clear()
        self.next_run_time = None
        if not self.schedule_config.get('enabled'):
            return

        hour, minute = self._random_time_in_range()
        time_str = f"{hour:02d}:{minute:02d}"
        today = datetime.now().date()
        run_at = datetime.combine(today, datetime.strptime(time_str, "%H:%M").time())
        if run_at <= datetime.now():
            run_at += timedelta(days=1)
        self.next_run_time = run_at
        schedule.every().day.at(time_str).do(self._trigger_daily_sign_in)
        self.log_scheduler(f"已安排下次签到: {self.next_run_time.strftime('%Y-%m-%d %H:%M')}")

    def _trigger_daily_sign_in(self):
        self.log_scheduler("到达定时签到时间，开始执行")
        threading.Thread(target=self._execute_daily_sign_in, daemon=True).start()

    def _execute_daily_sign_in(self):
        if not self.accounts:
            self.log_scheduler("定时签到跳过：无账号")
            self.apply_schedule()
            return
        self.log_scheduler("===== 定时签到开始 =====")
        for account in self.accounts:
            self.sign_in_single(account, self.log_scheduler)
            time.sleep(2)
        self.log_scheduler("===== 定时签到完成 =====")
        self.apply_schedule()

    def load_accounts(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.accounts = json.load(f)
            except:
                self.accounts = []
        else:
            self.accounts = []

    def save_accounts(self):
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.accounts, f, ensure_ascii=False, indent=2)
            return True
        except:
            return False

    def load_schedule_config(self):
        if os.path.exists(self.schedule_file):
            try:
                with open(self.schedule_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {'enabled': False, 'start_time': '08:00', 'end_time': '10:00', 'auto_start': False}

    def save_schedule_config(self):
        try:
            with open(self.schedule_file, 'w', encoding='utf-8') as f:
                json.dump(self.schedule_config, f, ensure_ascii=False, indent=2)
            return True
        except:
            return False

    def create_widgets(self):
        toolbar = tk.Frame(self.root, bg='#f0f0f0', height=50)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        tk.Button(toolbar, text="添加账号", command=self.add_account, bg='#4CAF50', fg='white',
                  font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="编辑账号", command=self.edit_account, bg='#2196F3', fg='white',
                  font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="删除账号", command=self.delete_account, bg='#f44336', fg='white',
                  font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="刷新", command=self.refresh_table, bg='#FF9800', fg='white',
                  font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="导入CSV", command=self.import_csv, bg='#9C27B0', fg='white',
                  font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="导出CSV", command=self.export_csv, bg='#607D8B', fg='white',
                  font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="一键签到", command=self.batch_sign_in, bg='#00BCD4', fg='white',
                  font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="⏰定时任务", command=self.open_scheduler, bg='#FF5722', fg='white',
                  font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)

        search_frame = tk.Frame(toolbar)
        search_frame.pack(side=tk.RIGHT, padx=5)
        tk.Label(search_frame, text="搜索:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.search_accounts())
        tk.Entry(search_frame, textvariable=self.search_var, width=20).pack(side=tk.LEFT, padx=5)

        table_frame = tk.Frame(self.root)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = ("ID", "昵称", "Cookie", "备注")
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=20)
        self.tree.heading("ID", text="ID")
        self.tree.heading("昵称", text="昵称")
        self.tree.heading("Cookie", text="Cookie")
        self.tree.heading("备注", text="备注")
        self.tree.column("ID", width=50, anchor='center')
        self.tree.column("昵称", width=150, anchor='center')
        self.tree.column("Cookie", width=800)
        self.tree.column("备注", width=150)

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        self.tree.bind('<Double-1>', lambda e: self.edit_account())

        self.status_bar = tk.Label(self.root, text=f"共 {len(self.accounts)} 个账号", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def refresh_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for idx, account in enumerate(self.accounts, 1):
            self.tree.insert('', 'end', values=(idx, account.get('nickname',''), account.get('cookie',''), account.get('remark','')))
        self.status_bar.config(text=f"共 {len(self.accounts)} 个账号")

    def search_accounts(self):
        search_text = self.search_var.get().lower()
        for item in self.tree.get_children():
            self.tree.delete(item)
        idx=1
        for account in self.accounts:
            if search_text in account.get('nickname','').lower() or search_text in account.get('cookie','').lower() or search_text in account.get('remark','').lower():
                self.tree.insert('', 'end', values=(idx, account.get('nickname',''), account.get('cookie',''), account.get('remark','')))
                idx+=1

    def add_account(self):
        dialog = AccountDialog(self.root, "添加账号")
        self.root.wait_window(dialog)
        if dialog.result:
            self.accounts.append(dialog.result)
            self.save_accounts()
            self.refresh_table()

    def edit_account(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请选择一个账号")
            return
        item = self.tree.item(selection[0])
        idx = int(item['values'][0])-1
        dialog = AccountDialog(self.root, "编辑账号", self.accounts[idx])
        self.root.wait_window(dialog)
        if dialog.result:
            self.accounts[idx] = dialog.result
            self.save_accounts()
            self.refresh_table()

    def delete_account(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请选择账号")
            return
        if messagebox.askyesno("确认", "确定删除？"):
            idx = int(self.tree.item(selection[0])['values'][0])-1
            del self.accounts[idx]
            self.save_accounts()
            self.refresh_table()

    def import_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV","*.csv"),("所有","*.*")])
        if not file_path: return
        try:
            import csv
            with open(file_path,'r',encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    nick = row.get('nickname','').strip()
                    cookie = row.get('cookie','').strip()
                    if nick and cookie:
                        self.accounts.append({"nickname":nick,"cookie":cookie,"remark":row.get('remark','')})
            self.save_accounts()
            self.refresh_table()
            messagebox.showinfo("成功","导入完成")
        except:
            messagebox.showerror("错误","导入失败")

    def export_csv(self):
        file_path = filedialog.asksaveasfilename(defaultextension='.csv',filetypes=[("CSV","*.csv")])
        if not file_path: return
        import csv
        with open(file_path,'w',encoding='utf-8',newline='') as f:
            w = csv.writer(f)
            w.writerow(['nickname','cookie','remark'])
            for a in self.accounts:
                w.writerow([a.get('nickname'),a.get('cookie'),a.get('remark')])
        messagebox.showinfo("成功","导出完成")

    def parse_cookie(self,s):
        d={}
        for i in s.split(';'):
            i=i.strip()
            if '=' in i:
                k,v = i.split('=',1)
                d[k.strip()]=v.strip()
        return d

    def get_api_headers(self, cm_page_id='WebViewActivity'):
        return {
            'cm_no_encrypt_native_tag_20220105': 'false',
            'CMPageId': cm_page_id,
            'User-Agent': 'NeteaseMoyi/2.20.0.260305100204(195);Dalvik/2.1.0 (Linux; U; Android 16; PLQ110 Build/BP2A.250605.015)',
            'X-ER': '25788',
            'MConfig-Info': '{"TT5Fdk0jbjHC6OZ5":{"version":"9361408","appver":"2.20.0"}}',
            'X-MAM-CustomMark': 'okhttp',
            'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8',
        }

    def sign_in_single(self, acc, log_callback):
        nickname = acc.get('nickname', '未知')
        cookie_str = acc.get('cookie', '')

        try:
            log_callback(f"[{nickname}] 开始签到...")
            cookies = self.parse_cookie(cookie_str)

            headers = self.get_api_headers('moyi_signin@index')
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

    def batch_sign_in(self):
        if not self.accounts:
            messagebox.showwarning("提示","无账号")
            return

        sign_window = tk.Toplevel(self.root)
        sign_window.title("批量签到")
        sign_window.geometry("700x500")

        log_frame = tk.Frame(sign_window)
        log_frame.pack(fill='both', expand=1, padx=10, pady=10)
        log_text = scrolledtext.ScrolledText(log_frame, font=('Courier', 9))
        log_text.pack(fill='both', expand=1)

        def log(msg):
            log_text.insert('end', msg + '\n')
            log_text.see('end')
            log_text.update()

        def run():
            log("===== 开始签到 =====")
            for account in self.accounts:
                self.sign_in_single(account, log)
                time.sleep(2)
            log("===== 签到完成 =====")

        threading.Thread(target=run, daemon=True).start()

    def log_scheduler(self, message):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

    def scheduled_sign_in(self):
        self.log_scheduler("手动触发定时签到")
        threading.Thread(target=self._execute_daily_sign_in, daemon=True).start()

    def open_scheduler(self):
        scheduler_window = tk.Toplevel(self.root)
        scheduler_window.title("定时任务管理")
        scheduler_window.geometry("650x550")  # 已修复：窗口变大，正常显示
        scheduler_window.transient(self.root)

        main_frame = tk.Frame(scheduler_window, padx=25, pady=25)
        main_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(main_frame, text="⏰ 每日自动签到设置", font=('Arial', 14, 'bold')).pack(pady=10)

        status_frame = tk.LabelFrame(main_frame, text="当前状态", padx=15, pady=15)
        status_frame.pack(fill='x', pady=10)
        status_label = tk.Label(status_frame, text="🟢 运行中" if self.scheduler_running else "🔴 未运行",
                                font=('Arial', 12), fg='green' if self.scheduler_running else 'red')
        status_label.pack()
        next_run_label = tk.Label(status_frame, font=('Arial', 10), fg='#555')
        next_run_label.pack(pady=5)

        def refresh_status():
            status_label.config(
                text="🟢 运行中" if self.scheduler_running else "🔴 未运行",
                fg='green' if self.scheduler_running else 'red'
            )
            if self.schedule_config.get('enabled') and self.next_run_time:
                next_run_label.config(text=f"下次签到: {self.next_run_time.strftime('%Y-%m-%d %H:%M')}")
            elif self.schedule_config.get('enabled'):
                next_run_label.config(text="下次签到: 等待安排")
            else:
                next_run_label.config(text="下次签到: 未启用")

        refresh_status()

        time_frame = tk.LabelFrame(main_frame, text="随机时间区间", padx=15, pady=15)
        time_frame.pack(fill='x', pady=10)

        tk.Label(time_frame, text="开始时间：").grid(row=0, column=0, sticky='w')
        start_hour_var = tk.StringVar(value=self.schedule_config['start_time'].split(':')[0])
        start_min_var = tk.StringVar(value=self.schedule_config['start_time'].split(':')[1])
        tk.Spinbox(time_frame, from_=0, to=23, width=5, textvariable=start_hour_var).grid(row=0, column=1, padx=5)
        tk.Label(time_frame, text="时").grid(row=0, column=2)
        tk.Spinbox(time_frame, from_=0, to=59, width=5, textvariable=start_min_var).grid(row=0, column=3, padx=5)
        tk.Label(time_frame, text="分").grid(row=0, column=4)

        tk.Label(time_frame, text="结束时间：").grid(row=1, column=0, sticky='w')
        end_hour_var = tk.StringVar(value=self.schedule_config['end_time'].split(':')[0])
        end_min_var = tk.StringVar(value=self.schedule_config['end_time'].split(':')[1])
        tk.Spinbox(time_frame, from_=0, to=23, width=5, textvariable=end_hour_var).grid(row=1, column=1, padx=5)
        tk.Label(time_frame, text="时").grid(row=1, column=2)
        tk.Spinbox(time_frame, from_=0, to=59, width=5, textvariable=end_min_var).grid(row=1, column=3, padx=5)
        tk.Label(time_frame, text="分").grid(row=1, column=4)

        enable_var = tk.BooleanVar(value=self.schedule_config['enabled'])
        auto_var = tk.BooleanVar(value=self.schedule_config['auto_start'])
        tk.Checkbutton(main_frame, text="启用定时任务", variable=enable_var).pack(anchor='w', pady=5)
        tk.Checkbutton(main_frame, text="开机自动启动", variable=auto_var).pack(anchor='w', pady=5)

        def save():
            self.schedule_config['enabled'] = enable_var.get()
            self.schedule_config['auto_start'] = auto_var.get()
            sh, sm = int(start_hour_var.get()), int(start_min_var.get())
            eh, em = int(end_hour_var.get()), int(end_min_var.get())
            self.schedule_config['start_time'] = f"{sh:02d}:{sm:02d}"
            self.schedule_config['end_time'] = f"{eh:02d}:{em:02d}"
            self.save_schedule_config()
            if enable_var.get():
                self.apply_schedule()
                self.start_scheduler()
            else:
                schedule.clear()
                self.next_run_time = None
                self.stop_scheduler()
            refresh_status()
            messagebox.showinfo("成功", "配置已保存")

        tk.Button(main_frame, text="保存配置", command=save, bg='#4CAF50', fg='white', width=15).pack(pady=15)

    def start_scheduler(self):
        if self.scheduler_running:
            return
        self.scheduler_running = True
        def run():
            while self.scheduler_running:
                schedule.run_pending()
                time.sleep(1)
        self.scheduler_thread = threading.Thread(target=run, daemon=True)
        self.scheduler_thread.start()

    def stop_scheduler(self):
        self.scheduler_running = False


if __name__ == "__main__":
    root = tk.Tk()
    app = AccountManager(root)
    root.mainloop()
