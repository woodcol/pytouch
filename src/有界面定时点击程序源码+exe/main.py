import os
import sys
import serial
import time
import json
import threading
import timetool
from sys import version_info
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

def pythonVersion():
    return version_info.major

class SerialController:
    def __init__(self):
        self.serialT = None
        self.is_running = False
        self.operation_thread = None
        self.operation_completed = False
        
        # 引脚指令字典
        self.type2Pins = {1:['<AAAA>','<FFFF>'], 2:['<5555>','<FFFF>'], 3:['<0000>','<FFFF>']}
        
        # 配置参数
        self.serial_port = None
        self.target_time = 0
        self.tcount = 10000
        self.time_params = {
            'first_down': 60,
            'first_up': 60,
            'second_down': 60,
            'second_up': 60,
            'loop_down': 60,
            'loop_up': 60
        }
    
    def connect_serial(self, port):
        """连接串口"""
        try:
            if self.serialT and self.serialT.is_open:
                self.serialT.close()
                
            self.serial_port = port
            self.serialT = serial.Serial(port, 115200, timeout=0.5)
            time.sleep(2)
            self.send_cmd('@')
            self.read_port()
            self.send_cmd('<FFFF>')
            return True, f"串口 {port} 连接成功"
        except Exception as e:
            return False, f"串口连接失败：{e}"
    
    def disconnect_serial(self):
        """断开串口连接"""
        if self.serialT and self.serialT.is_open:
            self.serialT.close()
            self.serialT = None
    
    def read_port(self):
        """读取串口返回数据"""
        if not self.serialT or not self.serialT.is_open:
            return ""
        
        try:
            time.sleep(0.003)
            n = self.serialT.inWaiting()
            if n > 0:
                pstr = self.serialT.read(n)
                if pythonVersion() == 2:
                    return pstr
                else:
                    return pstr.decode("utf-8", errors="ignore")
        except Exception as e:
            print(f'读取串口失败：{e}')
        return ""
    
    def send_cmd(self, pcmd):
        """发送串口指令"""
        if not self.serialT or not self.serialT.is_open:
            return 0
        
        try:
            back = None
            if pythonVersion() > 2:
                back = self.serialT.write(pcmd.encode())
            else:
                back = self.serialT.write(pcmd)
            self.serialT.flush()
            return back
        except Exception as e:
            print(f'发送指令失败：{e}')
            return 0
    
    def down_pin(self, n):
        """按下引脚"""
        self.send_cmd(self.type2Pins[n][0])
    
    def up_pin(self, n):
        """抬起引脚"""
        self.send_cmd(self.type2Pins[n][1])
    
    def load_time_config(self, filename='timer.txt'):
        """加载时间配置文件"""
        try:
            with open(filename, 'r') as f:
                dat = f.read()
                configs = json.loads(dat)
            
            # 转换配置时间为毫秒级时间戳
            ttime = int(timetool.conventTimeFromStrConfig(configs['time']) * 1000)
            # 读取重复次数
            tcount = configs['tCount']
            
            self.target_time = ttime
            self.tcount = tcount
            
            return True, ttime, tcount
        except Exception as e:
            return False, 0, 10000
    
    def save_time_config(self, time_str, tcount, filename='timer.txt'):
        """保存时间配置到文件"""
        try:
            config = {
                'time': time_str,
                'tCount': tcount
            }
            
            with open(filename, 'w') as f:
                json.dump(config, f, indent=2)
            
            return True, "时间配置保存成功"
        except Exception as e:
            return False, f"保存失败：{e}"
    
    def set_time_params(self, params):
        """设置时间参数"""
        self.time_params = params.copy()
    
    def format_time_string(self, year, month, day, hour, minute, second, millisecond):
        """将时间参数格式化为字符串"""
        # 格式: "2026-01-27|17:27:00!005"
        time_str = f"{year}-{month:02d}-{day:02d}|{hour:02d}:{minute:02d}:{second:02d}!{millisecond:03d}"
        return time_str
    
    def start_timing_operation(self, log_callback=None):
        """开始定时操作"""
        self.is_running = True
        self.operation_completed = False
        
        def run_operation():
            try:
                target_datetime = datetime.fromtimestamp(self.target_time/1000)
                if log_callback:
                    log_callback(f"等待目标时间: {target_datetime.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
                    log_callback(f"循环次数: {self.tcount}")
                
                # 计算等待时间
                now = time.time() * 1000
                wait_time = self.target_time - now
                
                if wait_time > 0:
                    if log_callback:
                        log_callback(f"等待 {wait_time/1000:.2f} 秒后开始执行...")
                    time.sleep(wait_time / 1000.0)
                
                while self.is_running and not self.operation_completed:
                    nowtime = int(time.time() * 1000)
                    
                    # 到达触发时间且未执行过
                    if not self.operation_completed and self.target_time <= nowtime:
                        if log_callback:
                            log_callback("开始执行按键操作...")
                        
                        # 第1次按键
                        if log_callback:
                            log_callback(f"第1次按下 ({self.time_params['first_down']}ms)")
                        self.down_pin(3)
                        time.sleep(self.time_params['first_down'] / 1000.0)
                        
                        if log_callback:
                            log_callback(f"第1次抬起 ({self.time_params['first_up']}ms)")
                        self.up_pin(3)
                        time.sleep(self.time_params['first_up'] / 1000.0)
                        
                        # 第2次按键
                        if log_callback:
                            log_callback(f"第2次按下 ({self.time_params['second_down']}ms)")
                        self.down_pin(3)
                        time.sleep(self.time_params['second_down'] / 1000.0)
                        
                        if log_callback:
                            log_callback(f"第2次抬起 ({self.time_params['second_up']}ms)")
                        self.up_pin(3)
                        time.sleep(self.time_params['second_up'] / 1000.0)
                        
                        # 循环按键
                        if log_callback:
                            log_callback(f"开始循环按键 ({self.tcount}次)")
                        
                        for i in range(self.tcount):
                            if not self.is_running:
                                break
                            
                            if (i + 1) % 1000 == 0 and log_callback:
                                log_callback(f"正在执行第 {i+1}/{self.tcount} 次循环")
                            
                            self.down_pin(3)
                            time.sleep(self.time_params['loop_down'] / 1000.0)
                            self.up_pin(3)
                            time.sleep(self.time_params['loop_up'] / 1000.0)
                        
                        self.operation_completed = True
                        
                        if log_callback:
                            log_callback("所有按键操作执行完成")
                        break
                    
                    time.sleep(0.001)
                
                if log_callback and not self.operation_completed:
                    log_callback("操作已停止")
                    
            except Exception as e:
                if log_callback:
                    log_callback(f"执行过程中出错：{e}")
            finally:
                self.is_running = False
        
        self.operation_thread = threading.Thread(target=run_operation)
        self.operation_thread.daemon = True
        self.operation_thread.start()
    
    def stop_operation(self):
        """停止操作"""
        self.is_running = False
        if self.operation_thread:
            self.operation_thread.join(timeout=1)


class DateTimePicker:
    """日期时间选择器"""
    def __init__(self, parent, label_text="选择时间:"):
        self.frame = ttk.LabelFrame(parent, text=label_text, padding="10")
        
        # 获取当前时间
        now = datetime.now()
        
        # 年份选择 (2024-2030)
        ttk.Label(self.frame, text="年:").grid(row=0, column=0, padx=2)
        self.year_var = tk.IntVar(value=now.year)
        self.year_spin = ttk.Spinbox(self.frame, from_=2024, to=2030, 
                                    textvariable=self.year_var, width=6)
        self.year_spin.grid(row=0, column=1, padx=2)
        
        # 月份选择
        ttk.Label(self.frame, text="月:").grid(row=0, column=2, padx=2)
        self.month_var = tk.IntVar(value=now.month)
        self.month_spin = ttk.Spinbox(self.frame, from_=1, to=12, 
                                     textvariable=self.month_var, width=4)
        self.month_spin.grid(row=0, column=3, padx=2)
        
        # 日期选择
        ttk.Label(self.frame, text="日:").grid(row=0, column=4, padx=2)
        self.day_var = tk.IntVar(value=now.day)
        self.day_spin = ttk.Spinbox(self.frame, from_=1, to=31, 
                                   textvariable=self.day_var, width=4)
        self.day_spin.grid(row=0, column=5, padx=2)
        
        # 小时选择
        ttk.Label(self.frame, text="时:").grid(row=1, column=0, padx=2, pady=(10, 0))
        self.hour_var = tk.IntVar(value=now.hour)
        self.hour_spin = ttk.Spinbox(self.frame, from_=0, to=23, 
                                    textvariable=self.hour_var, width=4)
        self.hour_spin.grid(row=1, column=1, padx=2, pady=(10, 0))
        
        # 分钟选择
        ttk.Label(self.frame, text="分:").grid(row=1, column=2, padx=2, pady=(10, 0))
        self.minute_var = tk.IntVar(value=now.minute)
        self.minute_spin = ttk.Spinbox(self.frame, from_=0, to=59, 
                                      textvariable=self.minute_var, width=4)
        self.minute_spin.grid(row=1, column=3, padx=2, pady=(10, 0))
        
        # 秒选择
        ttk.Label(self.frame, text="秒:").grid(row=1, column=4, padx=2, pady=(10, 0))
        self.second_var = tk.IntVar(value=now.second)
        self.second_spin = ttk.Spinbox(self.frame, from_=0, to=59, 
                                      textvariable=self.second_var, width=4)
        self.second_spin.grid(row=1, column=5, padx=2, pady=(10, 0))
        
        # 毫秒选择
        ttk.Label(self.frame, text="毫秒:").grid(row=2, column=0, padx=2, pady=(10, 0))
        self.millisecond_var = tk.IntVar(value=5)
        self.millisecond_spin = ttk.Spinbox(self.frame, from_=0, to=999, 
                                           textvariable=self.millisecond_var, width=5)
        self.millisecond_spin.grid(row=2, column=1, padx=2, pady=(10, 0))
        
        # 当前时间按钮
        ttk.Button(self.frame, text="当前时间", 
                  command=self.set_current_time, width=10).grid(row=2, column=2, columnspan=2, padx=2, pady=(10, 0))
        
        # 预览标签
        ttk.Label(self.frame, text="时间格式:").grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))
        self.preview_label = ttk.Label(self.frame, text="", font=("Courier", 9))
        self.preview_label.grid(row=3, column=2, columnspan=4, sticky=tk.W, pady=(10, 0))
        
        # 绑定更新事件
        for var in [self.year_var, self.month_var, self.day_var, 
                   self.hour_var, self.minute_var, self.second_var, self.millisecond_var]:
            var.trace('w', lambda *args: self.update_preview())
        
        self.update_preview()
    
    def grid(self, **kwargs):
        """放置框架"""
        return self.frame.grid(**kwargs)
    
    def set_current_time(self):
        """设置为当前时间"""
        now = datetime.now()
        self.year_var.set(now.year)
        self.month_var.set(now.month)
        self.day_var.set(now.day)
        self.hour_var.set(now.hour)
        self.minute_var.set(now.minute)
        self.second_var.set(now.second)
        self.millisecond_var.set(now.microsecond // 1000)
    
    def update_preview(self):
        """更新时间预览"""
        try:
            time_str = self.get_time_string()
            self.preview_label.config(text=time_str)
        except:
            self.preview_label.config(text="无效时间")
    
    def get_time_string(self):
        """获取时间字符串"""
        year = self.year_var.get()
        month = self.month_var.get()
        day = self.day_var.get()
        hour = self.hour_var.get()
        minute = self.minute_var.get()
        second = self.second_var.get()
        millisecond = self.millisecond_var.get()
        
        # 验证日期是否有效
        datetime(year, month, day, hour, minute, second)
        
        # 格式: "2026-01-27|17:27:00!005"
        time_str = f"{year}-{month:02d}-{day:02d}|{hour:02d}:{minute:02d}:{second:02d}!{millisecond:03d}"
        return time_str
    
    def get_datetime(self):
        """获取datetime对象"""
        year = self.year_var.get()
        month = self.month_var.get()
        day = self.day_var.get()
        hour = self.hour_var.get()
        minute = self.minute_var.get()
        second = self.second_var.get()
        millisecond = self.millisecond_var.get()
        
        return datetime(year, month, day, hour, minute, second, millisecond * 1000)
    
    def get_timestamp_ms(self):
        """获取毫秒时间戳"""
        dt = self.get_datetime()
        return int(dt.timestamp() * 1000)
    
    def set_from_time_string(self, time_str):
        """从时间字符串设置"""
        try:
            # 解析格式: "2026-01-27|17:27:00!005"
            date_part, time_part = time_str.split('|')
            time_main, millisecond_part = time_part.split('!')
            
            # 解析日期
            year, month, day = map(int, date_part.split('-'))
            
            # 解析时间
            hour, minute, second = map(int, time_main.split(':'))
            
            # 解析毫秒
            millisecond = int(millisecond_part)
            
            # 设置值
            self.year_var.set(year)
            self.month_var.set(month)
            self.day_var.set(day)
            self.hour_var.set(hour)
            self.minute_var.set(minute)
            self.second_var.set(second)
            self.millisecond_var.set(millisecond)
            
            self.update_preview()
            return True
        except:
            return False


class SerialControlApp:
    def __init__(self, root):
        self.root = root
        self.root.title("按键定时控制器")
        self.root.geometry("650x750")
        
        self.serial_controller = SerialController()
        
        # 创建界面
        self.create_widgets()
        
        # 尝试加载配置文件
        self.load_config()
        
        # 更新界面显示
        self.update_display()
    
    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        row = 0
        
        # 串口配置区域
        ttk.Label(main_frame, text="串口配置", font=("Arial", 12, "bold")).grid(
            row=row, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))
        row += 1
        
        ttk.Label(main_frame, text="串口号:").grid(row=row, column=0, sticky=tk.W, padx=(0, 10))
        self.port_var = tk.StringVar(value="COM3")
        port_entry = ttk.Entry(main_frame, textvariable=self.port_var, width=15)
        port_entry.grid(row=row, column=1, sticky=tk.W)
        
        self.connect_btn = ttk.Button(main_frame, text="连接串口", command=self.connect_serial)
        self.connect_btn.grid(row=row, column=2, padx=(10, 0))
        row += 1
        
        self.status_label = ttk.Label(main_frame, text="状态: 未连接", foreground="red")
        self.status_label.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(5, 15))
        row += 1
        
        # 日期时间选择器
        self.datetime_picker = DateTimePicker(main_frame, "设置目标时间")
        self.datetime_picker.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))
        row += 1
        
        # 循环次数
        ttk.Label(main_frame, text="循环次数:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.tcount_var = tk.IntVar(value=1000000)
        tcount_spin = ttk.Spinbox(main_frame, from_=1, to=10000000, 
                                 textvariable=self.tcount_var, width=15)
        tcount_spin.grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # 时间参数配置区域
        ttk.Label(main_frame, text="按键时间参数 (单位:毫秒)", font=("Arial", 12, "bold")).grid(
            row=row, column=0, columnspan=3, sticky=tk.W, pady=(10, 10))
        row += 1
        
        # 创建时间参数输入框
        self.time_params = {}
        time_labels = [
            ("第1次按下时间:", "first_down", 60),
            ("第1次抬起时间:", "first_up", 60),
            ("第2次按下时间:", "second_down", 60),
            ("第2次抬起时间:", "second_up", 60),
            ("循环按下时间:", "loop_down", 60),
            ("循环抬起时间:", "loop_up", 60)
        ]
        
        for label_text, param_name, default_value in time_labels:
            ttk.Label(main_frame, text=label_text).grid(row=row, column=0, sticky=tk.W, pady=3)
            var = tk.IntVar(value=default_value)
            spinbox = ttk.Spinbox(main_frame, from_=10, to=10000, 
                                 textvariable=var, width=10)
            spinbox.grid(row=row, column=1, sticky=tk.W, pady=3)
            self.time_params[param_name] = var
            row += 1
        
        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row, column=0, columnspan=3, pady=(20, 10))
        row += 1
        
        self.start_btn = ttk.Button(button_frame, text="开始执行", 
                                   command=self.start_operation, width=12)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(button_frame, text="停止执行", 
                                  command=self.stop_operation, 
                                  state=tk.DISABLED, width=12)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="保存配置", 
                  command=self.save_config, width=12).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="加载配置", 
                  command=self.load_config, width=12).pack(side=tk.LEFT, padx=5)
        
        # 状态信息区域
        info_frame = ttk.LabelFrame(main_frame, text="状态信息", padding="10")
        info_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 10))
        row += 1
        
        self.time_info_label = ttk.Label(info_frame, text="目标时间: 未设置")
        self.time_info_label.grid(row=0, column=0, sticky=tk.W)
        
        self.countdown_label = ttk.Label(info_frame, text="倒计时: --")
        self.countdown_label.grid(row=0, column=1, sticky=tk.W, padx=(20, 0))
        
        # 日志区域
        ttk.Label(main_frame, text="执行日志", font=("Arial", 12, "bold")).grid(
            row=row, column=0, columnspan=3, sticky=tk.W, pady=(10, 5))
        row += 1
        
        # 日志文本框
        log_frame = ttk.Frame(main_frame)
        log_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = tk.Text(log_frame, height=8, wrap=tk.WORD, font=("Courier", 9))
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 清空日志按钮
        ttk.Button(log_frame, text="清空日志", 
                  command=self.clear_log).grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
    
    def connect_serial(self):
        """连接串口"""
        port = self.port_var.get()
        
        success, message = self.serial_controller.connect_serial(port)
        
        if success:
            self.status_label.config(text=f"状态: 已连接到 {port}", foreground="green")
            self.connect_btn.config(text="断开连接", command=self.disconnect_serial)
            self.log_message(message)
        else:
            messagebox.showerror("连接失败", message)
            self.log_message(f"连接失败: {message}")
    
    def disconnect_serial(self):
        """断开串口连接"""
        self.serial_controller.disconnect_serial()
        self.status_label.config(text="状态: 未连接", foreground="red")
        self.connect_btn.config(text="连接串口", command=self.connect_serial)
        self.log_message("串口已断开")
    
    def start_operation(self):
        """开始执行操作"""
        # 验证串口连接
        if not self.serial_controller.serialT or not self.serial_controller.serialT.is_open:
            messagebox.showwarning("警告", "请先连接串口")
            return
        
        # 获取时间字符串
        try:
            time_str = self.datetime_picker.get_time_string()
            target_datetime = self.datetime_picker.get_datetime()
            target_timestamp_ms = self.datetime_picker.get_timestamp_ms()
            
            # 更新状态信息
            self.time_info_label.config(
                text=f"目标时间: {target_datetime.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}"
            )
            
        except ValueError as e:
            messagebox.showerror("错误", f"时间设置无效: {e}")
            return
        
        # 获取时间参数
        time_params = {}
        for param_name, var in self.time_params.items():
            time_params[param_name] = var.get()
        
        # 设置时间参数
        self.serial_controller.set_time_params(time_params)
        
        # 保存时间配置
        tcount = self.tcount_var.get()
        
        success, message = self.serial_controller.save_time_config(time_str, tcount)
        if not success:
            messagebox.showwarning("警告", f"保存时间配置失败：{message}")
            return
        
        # 设置目标时间戳
        self.serial_controller.target_time = target_timestamp_ms
        self.serial_controller.tcount = tcount
        
        # 计算倒计时
        now_ms = int(time.time() * 1000)
        countdown_ms = target_timestamp_ms - now_ms
        
        if countdown_ms < 0:
            if messagebox.askyesno("时间已过", "设置的目标时间已经过去，是否立即开始执行？"):
                self.serial_controller.target_time = now_ms + 1000  # 1秒后开始
                countdown_ms = 1000
            else:
                return
        
        # 更新按钮状态
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        # 开始执行
        self.log_message(f"开始执行定时操作，倒计时: {countdown_ms/1000:.2f}秒")
        self.serial_controller.start_timing_operation(self.log_message)
        
        # 开始倒计时更新
        self.start_countdown(countdown_ms)
    
    def start_countdown(self, countdown_ms):
        """开始倒计时"""
        if countdown_ms <= 0:
            self.countdown_label.config(text="倒计时: 00:00:00")
            return
        
        # 更新倒计时显示
        seconds = countdown_ms / 1000.0
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        self.countdown_label.config(text=f"倒计时: {hours:02d}:{minutes:02d}:{secs:02d}")
        
        # 每秒更新一次
        if self.serial_controller.is_running and countdown_ms > 0:
            self.root.after(1000, self.start_countdown, countdown_ms - 1000)
    
    def check_operation_status(self):
        """检查操作执行状态"""
        if self.serial_controller.is_running:
            self.root.after(100, self.check_operation_status)
        else:
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.countdown_label.config(text="倒计时: --")
    
    def stop_operation(self):
        """停止操作"""
        self.serial_controller.stop_operation()
        self.log_message("操作已停止")
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.countdown_label.config(text="倒计时: --")
    
    def save_config(self):
        """保存配置"""
        try:
            # 获取时间字符串
            time_str = self.datetime_picker.get_time_string()
            
            config = {
                'serial_port': self.port_var.get(),
                'time': time_str,
                'tCount': self.tcount_var.get(),
                'time_params': {name: var.get() for name, var in self.time_params.items()}
            }
            
            with open('ui_config.json', 'w') as f:
                json.dump(config, f, indent=2)
            
            self.log_message("配置已保存到 ui_config.json")
            messagebox.showinfo("成功", "配置保存成功")
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败：{e}")
    
    def load_config(self):
        """加载配置"""
        try:
            if os.path.exists('ui_config.json'):
                with open('ui_config.json', 'r') as f:
                    config = json.load(f)
                
                self.port_var.set(config.get('serial_port', 'COM3'))
                self.tcount_var.set(config.get('tCount', 1000000))
                
                time_params = config.get('time_params', {})
                for param_name, var in self.time_params.items():
                    if param_name in time_params:
                        var.set(time_params[param_name])
                
                # 加载时间设置
                time_str = config.get('time', '')
                if time_str:
                    self.datetime_picker.set_from_time_string(time_str)
                
                self.log_message("配置已从 ui_config.json 加载")
                self.update_display()
        except Exception as e:
            self.log_message(f"加载配置失败：{e}")
    
    def update_display(self):
        """更新显示"""
        # 加载timer.txt文件
        success, target_time, tcount = self.serial_controller.load_time_config()
        if success:
            # 将时间戳转换为datetime对象
            try:
                dt = datetime.fromtimestamp(target_time / 1000)
                # 生成时间字符串
                time_str = f"{dt.year}-{dt.month:02d}-{dt.day:02d}|{dt.hour:02d}:{dt.minute:02d}:{dt.second:02d}!{dt.microsecond//1000:03d}"
                self.datetime_picker.set_from_time_string(time_str)
            except:
                pass
            
            self.tcount_var.set(tcount)
            
            # 更新状态信息
            if success and target_time > 0:
                dt = datetime.fromtimestamp(target_time / 1000)
                self.time_info_label.config(
                    text=f"目标时间: {dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}"
                )
    
    def log_message(self, message):
        """添加日志消息"""
        timestamp = time.strftime("%H:%M:%S", time.localtime())
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        
        # 保持日志不超过500行
        lines = int(self.log_text.index('end-1c').split('.')[0])
        if lines > 500:
            self.log_text.delete(1.0, 2.0)
    
    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)
    
    def on_closing(self):
        """关闭窗口时的处理"""
        self.serial_controller.stop_operation()
        self.serial_controller.disconnect_serial()
        self.root.destroy()


def main():
    """主函数"""
    root = tk.Tk()
    app = SerialControlApp(root)
    
    # 设置关闭窗口事件
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # 启动主循环
    root.mainloop()


if __name__ == '__main__':
    main()