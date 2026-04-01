#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import serial
import time
import tkinter as tk
from tkinter import ttk  # 添加这一行
from tkinter import messagebox
from sys import version_info
import threading
import serial.tools.list_ports
import json
import os.path

isTest = False
SERIALOBJ1 = None
SERIALOBJ2 = None

# 配置文件路径
CONFIG_FILE = "serial_config.json"


def pythonVersion():
    return version_info.major


def sendcmd(t, cmd):
    """发送命令到串口 - 优化为立即发送"""
    try:
        sendstr = cmd
        print(f"立即发送: {sendstr}")
        if pythonVersion() > 2:
            t.write(sendstr.encode())
        else:
            t.write(sendstr.encode())
        t.flush()  # 立即刷新缓冲区
    except Exception as e:
        print(f"发送错误: {e}")
        raise e


def find_ch340_ports():
    """查找所有包含CH340的串口"""
    ch340_ports = []
    ports = serial.tools.list_ports.comports()
    
    for port in ports:
        # 检查设备描述或名称中是否包含CH340
        if (port.description and "CH340" in port.description) or \
           (port.manufacturer and "CH340" in port.manufacturer) or \
           ("CH340" in port.device):
            ch340_ports.append(port.device)
    
    return ch340_ports


def save_config(port1, port2):
    """保存串口配置"""
    config = {
        "port1": port1,
        "port2": port2
    }
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f)
    except Exception as e:
        print(f"保存配置失败: {e}")


def load_config():
    """加载串口配置"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                return config.get("port1", ""), config.get("port2", "")
    except Exception as e:
        print(f"加载配置失败: {e}")
    return "", ""


class SerialApp:
    def __init__(self, root):
        self.root = root
        self.root.title("fengmm521.taobao.com")
        self.root.geometry("400x200")  # 增加窗口高度以容纳两个串口
        self.root.resizable(False, False)

        self.serial_obj1 = None
        self.serial_obj2 = None
        self.is_connected1 = False
        self.is_connected2 = False
        
        # 用于快速发送的标志
        self.send_lock = threading.Lock()

        # 设置样式
        self.root.configure(bg='#f0f0f0')
        
        # 主框架
        main_frame = tk.Frame(root, bg='#f0f0f0')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 串口1区域
        serial1_frame = tk.Frame(main_frame, bg='#f0f0f0')
        serial1_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(serial1_frame, text="串口1:", bg='#f0f0f0', font=("Arial", 9), width=6).pack(side=tk.LEFT, padx=(0, 5))
        
        self.port1_var = tk.StringVar(value="")
        self.port1_combo = tk.ttk.Combobox(serial1_frame, textvariable=self.port1_var, width=12, font=("Arial", 9))
        self.port1_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        # 连接/断开按钮
        self.connect1_btn = tk.Button(
            serial1_frame,
            text="打开",
            bg="#ff4444",
            fg="white",
            font=("Arial", 9, "bold"),
            height=1,
            width=8,
            command=lambda: self.toggle_serial(1),
            relief=tk.RAISED,
            bd=1
        )
        self.connect1_btn.pack(side=tk.LEFT)
        
        # 状态标签
        self.status1_label = tk.Label(
            serial1_frame,
            text="未连接",
            bg='#f0f0f0',
            fg="#666666",
            font=("Arial", 9),
            anchor=tk.W,
            width=15
        )
        self.status1_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # 串口2区域
        serial2_frame = tk.Frame(main_frame, bg='#f0f0f0')
        serial2_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(serial2_frame, text="串口2:", bg='#f0f0f0', font=("Arial", 9), width=6).pack(side=tk.LEFT, padx=(0, 5))
        
        self.port2_var = tk.StringVar(value="")
        self.port2_combo = tk.ttk.Combobox(serial2_frame, textvariable=self.port2_var, width=12, font=("Arial", 9))
        self.port2_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        # 连接/断开按钮
        self.connect2_btn = tk.Button(
            serial2_frame,
            text="打开",
            bg="#ff4444",
            fg="white",
            font=("Arial", 9, "bold"),
            height=1,
            width=8,
            command=lambda: self.toggle_serial(2),
            relief=tk.RAISED,
            bd=1
        )
        self.connect2_btn.pack(side=tk.LEFT)
        
        # 状态标签
        self.status2_label = tk.Label(
            serial2_frame,
            text="未连接",
            bg='#f0f0f0',
            fg="#666666",
            font=("Arial", 9),
            anchor=tk.W,
            width=15
        )
        self.status2_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # 刷新串口按钮
        refresh_btn = tk.Button(
            main_frame,
            text="刷新串口列表",
            bg="#9e9e9e",
            fg="white",
            font=("Arial", 9),
            command=self.refresh_ports
        )
        refresh_btn.pack(pady=(0, 10))
        
        # 控制按钮区域
        button_frame = tk.Frame(main_frame, bg='#f0f0f0')
        button_frame.pack(fill=tk.BOTH, expand=True)
        
        # 配置grid列权重
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        button_frame.grid_columnconfigure(2, weight=1)
        
        # 按钮 5
        self.btn_5 = tk.Button(
            button_frame, 
            text="5", 
            font=("Arial", 40, "bold"),
            bg="#4CAF50", 
            fg="white",
            activebackground="#45a049",
            relief=tk.RAISED,
            bd=2,
            cursor="hand2"
        )
        self.btn_5.grid(row=0, column=0, sticky="nsew", padx=3, pady=3)
        self.btn_5.bind('<ButtonPress-1>', lambda e, cmd='5': self.quick_send(cmd))
        
        # 按钮 6
        self.btn_6 = tk.Button(
            button_frame, 
            text="6", 
            font=("Arial", 40, "bold"),
            bg="#2196F3", 
            fg="white",
            activebackground="#0b7dda",
            relief=tk.RAISED,
            bd=2,
            cursor="hand2"
        )
        self.btn_6.grid(row=0, column=1, sticky="nsew", padx=3, pady=3)
        self.btn_6.bind('<ButtonPress-1>', lambda e, cmd='6': self.quick_send(cmd))
        
        # 按钮 7
        self.btn_7 = tk.Button(
            button_frame, 
            text="7", 
            font=("Arial", 40, "bold"),
            bg="#ff9800", 
            fg="white",
            activebackground="#e68900",
            relief=tk.RAISED,
            bd=2,
            cursor="hand2"
        )
        self.btn_7.grid(row=0, column=2, sticky="nsew", padx=3, pady=3)
        self.btn_7.bind('<ButtonPress-1>', lambda e, cmd='7': self.quick_send(cmd))
        
        # 设置按钮的最小高度
        button_frame.grid_rowconfigure(0, weight=1)
        
        # 初始设置按钮状态为禁用
        self.set_buttons_state(False)
        
        # 刷新串口列表
        self.refresh_ports()
        
        # 关闭窗口时的处理
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 启动时自动连接CH340串口
        self.root.after(100, self.auto_connect_ch340)
    
    def update_status(self, port_num, message, is_error=False):
        """更新状态标签"""
        if port_num == 1:
            self.status1_label.config(text=message, fg="#ff4444" if is_error else "#4CAF50")
        else:
            self.status2_label.config(text=message, fg="#ff4444" if is_error else "#4CAF50")
    
    def refresh_ports(self):
        """刷新可用的串口列表"""
        ports = serial.tools.list_ports.comports()
        port_list = [port.device for port in ports]
        
        # 更新下拉列表
        self.port1_combo['values'] = port_list
        self.port2_combo['values'] = port_list
        
        # 如果当前选中的串口不在列表中，清空
        if self.port1_var.get() not in port_list:
            self.port1_var.set("")
        if self.port2_var.get() not in port_list:
            self.port2_var.set("")
    
    def auto_connect_ch340(self):
        """自动连接CH340串口"""
        ch340_ports = find_ch340_ports()
        
        if len(ch340_ports) >= 1:
            # 连接第一个CH340
            self.port1_var.set(ch340_ports[0])
            self.open_serial(1, silent=True)
        
        if len(ch340_ports) >= 2:
            # 连接第二个CH340
            self.port2_var.set(ch340_ports[1])
            self.open_serial(2, silent=True)
        elif len(ch340_ports) == 0:
            # 没有找到CH340，尝试加载上次的配置
            last_port1, last_port2 = load_config()
            if last_port1:
                self.port1_var.set(last_port1)
            if last_port2:
                self.port2_var.set(last_port2)
            
            # 显示提示信息
            self.update_status(1, "未找到CH340", True)
            self.update_status(2, "未找到CH340", True)
    
    def set_buttons_state(self, enabled):
        """设置按钮的启用/禁用状态"""
        state = tk.NORMAL if enabled else tk.DISABLED
        self.btn_5.config(state=state)
        self.btn_6.config(state=state)
        self.btn_7.config(state=state)
    
    def quick_send(self, cmd):
        """立即向所有已连接的串口发送命令"""
        with self.send_lock:
            sent_count = 0
            
            # 向串口1发送
            if self.is_connected1 and self.serial_obj1 and self.serial_obj1.is_open:
                try:
                    sendcmd(self.serial_obj1, f"{cmd}\n")
                    sent_count += 1
                except Exception as e:
                    self.update_status(1, f"发送失败", True)
            
            # 向串口2发送
            if self.is_connected2 and self.serial_obj2 and self.serial_obj2.is_open:
                try:
                    sendcmd(self.serial_obj2, f"{cmd}\n")
                    sent_count += 1
                except Exception as e:
                    self.update_status(2, f"发送失败", True)
            
            if sent_count > 0:
                self.update_status(1, f"已发送{cmd}", False)
                if self.is_connected2:
                    self.update_status(2, f"已发送{cmd}", False)
            else:
                self.update_status(1, "无可用串口", True)
                self.update_status(2, "无可用串口", True)
    
    def toggle_serial(self, port_num):
        """打开或关闭指定串口"""
        if port_num == 1:
            if not self.is_connected1:
                self.open_serial(1, silent=False)
            else:
                self.close_serial(1)
        else:
            if not self.is_connected2:
                self.open_serial(2, silent=False)
            else:
                self.close_serial(2)
    
    def open_serial(self, port_num, silent=False):
        """打开指定串口"""
        if port_num == 1:
            port_var = self.port1_var
            port_combo = self.port1_combo
            connect_btn = self.connect1_btn
            status_prefix = "串口1"
        else:
            port_var = self.port2_var
            port_combo = self.port2_combo
            connect_btn = self.connect2_btn
            status_prefix = "串口2"
        
        port = port_var.get().strip()
        if not port:
            if not silent:
                messagebox.showerror("错误", f"请选择{status_prefix}")
            self.update_status(port_num, "未选择串口", True)
            return
        
        try:
            serial_obj = serial.Serial(
                port, 
                115200, 
                timeout=0,
                write_timeout=0.001,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            
            if port_num == 1:
                self.serial_obj1 = serial_obj
                self.is_connected1 = True
                self.connect1_btn.config(text="断开", bg="#4CAF50")
                self.port1_combo.config(state=tk.DISABLED)
                self.update_status(1, "已连接", False)
            else:
                self.serial_obj2 = serial_obj
                self.is_connected2 = True
                self.connect2_btn.config(text="断开", bg="#4CAF50")
                self.port2_combo.config(state=tk.DISABLED)
                self.update_status(2, "已连接", False)
            
            # 保存配置
            save_config(self.port1_var.get(), self.port2_var.get())
            
            # 如果两个串口都连接了，启用按钮
            if self.is_connected1 or self.is_connected2:
                self.set_buttons_state(True)
            
        except Exception as e:
            self.update_status(port_num, "打开失败", True)
            if not silent:
                messagebox.showerror("错误", f"无法打开{status_prefix} {port}\n{str(e)}")
    
    def close_serial(self, port_num):
        """关闭指定串口"""
        if port_num == 1:
            if self.serial_obj1 and self.serial_obj1.is_open:
                try:
                    self.serial_obj1.close()
                except Exception as e:
                    print(f"关闭串口1时出错: {str(e)}")
            
            self.serial_obj1 = None
            self.is_connected1 = False
            self.connect1_btn.config(text="打开", bg="#ff4444")
            self.port1_combo.config(state=tk.NORMAL)
            self.update_status(1, "已断开", True)
        else:
            if self.serial_obj2 and self.serial_obj2.is_open:
                try:
                    self.serial_obj2.close()
                except Exception as e:
                    print(f"关闭串口2时出错: {str(e)}")
            
            self.serial_obj2 = None
            self.is_connected2 = False
            self.connect2_btn.config(text="打开", bg="#ff4444")
            self.port2_combo.config(state=tk.NORMAL)
            self.update_status(2, "已断开", True)
        
        # 如果两个串口都断开了，禁用按钮
        if not self.is_connected1 and not self.is_connected2:
            self.set_buttons_state(False)
        
        # 保存配置
        save_config(self.port1_var.get(), self.port2_var.get())
    
    def on_closing(self):
        """关闭窗口时的清理工作"""
        # 保存配置
        save_config(self.port1_var.get(), self.port2_var.get())
        
        # 关闭串口
        if self.serial_obj1 and self.serial_obj1.is_open:
            try:
                self.serial_obj1.close()
            except:
                pass
        
        if self.serial_obj2 and self.serial_obj2.is_open:
            try:
                self.serial_obj2.close()
            except:
                pass
        
        self.root.destroy()


def main_gui():
    """启动GUI界面"""
    root = tk.Tk()
    app = SerialApp(root)
    root.mainloop()


if __name__ == '__main__':
    args = sys.argv
    if len(args) == 2 and args[1] == '--cli':
        # CLI模式保持原有功能
        dev = 'com3'
        t = serial.Serial(dev, 115200, timeout=1)
        SERIALOBJ = t
        if t:
            print(t.name)
            print(t.port)
            print(t.baudrate)
            print(t.bytesize)
            print(t.parity)
            print(t.stopbits)
            print(t.timeout)
            print(t.writeTimeout)
            print(t.xonxoff)
            print(t.rtscts)
            print(t.dsrdtr)
            print(t.interCharTimeout)
            print('-' * 10)
            time.sleep(1)
            sendcmd(t, '5\n')
            time.sleep(1)
            t.close()
        else:
            print('串口不存在')
    else:
        main_gui()