#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import serial
import time
import tkinter as tk
from tkinter import messagebox
from sys import version_info
import threading

isTest = False
SERIALOBJ = None


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


class SerialApp:
    def __init__(self, root):
        self.root = root
        self.root.title("fengmm521.taobao.com")
        self.root.geometry("320x150")  # 保持原窗口大小
        self.root.resizable(False, False)

        self.serial_obj = None
        self.is_connected = False
        
        # 用于快速发送的标志
        self.send_lock = threading.Lock()

        # 设置样式
        self.root.configure(bg='#f0f0f0')
        
        # 主框架
        main_frame = tk.Frame(root, bg='#f0f0f0')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 第一行：串口选择和连接按钮
        top_frame = tk.Frame(main_frame, bg='#f0f0f0')
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(top_frame, text="COM", bg='#f0f0f0', font=("Arial", 9)).pack(side=tk.LEFT, padx=(0, 5))
        
        self.port_var = tk.StringVar(value="3")
        self.port_entry = tk.Entry(top_frame, textvariable=self.port_var, width=5, font=("Arial", 9))
        self.port_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        # 连接/断开按钮
        self.connect_btn = tk.Button(
            top_frame,
            text="打开",
            bg="#ff4444",
            fg="white",
            font=("Arial", 9, "bold"),
            height=1,
            width=8,
            command=self.toggle_serial,
            relief=tk.RAISED,
            bd=1
        )
        self.connect_btn.pack(side=tk.LEFT)
        
        # 提示标签（在打开按钮右边）
        self.status_label = tk.Label(
            top_frame,
            text="",
            bg='#f0f0f0',
            fg="#000000",  # 黑色文字
            font=("Arial", 9),
            anchor=tk.W
        )
        self.status_label.pack(side=tk.LEFT, padx=(10, 0), fill=tk.X, expand=True)
        
        # 第二行：三个控制按钮 - 使用grid布局确保等宽等高
        button_frame = tk.Frame(main_frame, bg='#f0f0f0')
        button_frame.pack(fill=tk.BOTH, expand=True)
        
        # 配置grid列权重，让三列平均分配空间
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        button_frame.grid_columnconfigure(2, weight=1)
        
        # 按钮 5 - 文字放大并居中
        self.btn_5 = tk.Button(
            button_frame, 
            text="5", 
            font=("Arial", 40, "bold"),  # 字体从20增大到40
            bg="#4CAF50", 
            fg="white",
            activebackground="#45a049",
            relief=tk.RAISED,
            bd=2,
            cursor="hand2"
        )
        self.btn_5.grid(row=0, column=0, sticky="nsew", padx=3, pady=3)
        self.btn_5.bind('<ButtonPress-1>', lambda e, cmd='5': self.quick_send(cmd))
        
        # 按钮 6 - 文字放大并居中
        self.btn_6 = tk.Button(
            button_frame, 
            text="6", 
            font=("Arial", 40, "bold"),  # 字体从20增大到40
            bg="#2196F3", 
            fg="white",
            activebackground="#0b7dda",
            relief=tk.RAISED,
            bd=2,
            cursor="hand2"
        )
        self.btn_6.grid(row=0, column=1, sticky="nsew", padx=3, pady=3)
        self.btn_6.bind('<ButtonPress-1>', lambda e, cmd='6': self.quick_send(cmd))
        
        # 按钮 7 - 文字放大并居中
        self.btn_7 = tk.Button(
            button_frame, 
            text="7", 
            font=("Arial", 40, "bold"),  # 字体从20增大到40
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
        
        # 设置三个按钮的初始状态为禁用（未连接时）
        self.set_buttons_state(False)
        
        # 关闭窗口时的处理
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 启动时自动尝试打开串口（延迟执行，确保界面完全加载）
        self.root.after(100, self.auto_open_serial)
    
    def update_status(self, message):
        """更新状态标签"""
        self.status_label.config(text=message)
    
    def auto_open_serial(self):
        """启动时自动尝试打开串口"""
        self.open_serial(silent=True)
    
    def set_buttons_state(self, enabled):
        """设置按钮的启用/禁用状态"""
        state = tk.NORMAL if enabled else tk.DISABLED
        self.btn_5.config(state=state)
        self.btn_6.config(state=state)
        self.btn_7.config(state=state)
    
    def quick_send(self, cmd):
        """立即发送命令"""
        with self.send_lock:
            if not self.is_connected or not self.serial_obj:
                self.update_status("串口未连接")
                return
            
            if not self.serial_obj.is_open:
                self.update_status("串口未打开")
                return
            
            try:
                sendcmd(self.serial_obj, f"{cmd}\n")
                self.update_status(f"已发送{cmd}")
            except Exception as e:
                self.update_status(f"发送失败")
    
    def toggle_serial(self):
        """打开或关闭串口"""
        if not self.is_connected:
            self.open_serial(silent=False)
        else:
            self.close_serial()
    
    def open_serial(self, silent=False):
        """打开串口
        
        Args:
            silent: 是否静默模式（不显示错误弹窗）
        """
        port_num = self.port_var.get().strip()
        if not port_num:
            if not silent:
                messagebox.showerror("错误", "请输入串口号")
            self.update_status("串口打开失败")
            return
        
        port = f"COM{port_num}"
        
        try:
            self.serial_obj = serial.Serial(
                port, 
                115200, 
                timeout=0,
                write_timeout=0.001,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            self.is_connected = True
            
            # 更新按钮样式
            self.connect_btn.config(text="断开", bg="#4CAF50")
            self.port_entry.config(state=tk.DISABLED)
            
            # 启用控制按钮
            self.set_buttons_state(True)
            
            self.update_status("串口已连接")
            
        except Exception as e:
            self.serial_obj = None
            self.update_status("串口打开失败")
            if not silent:
                messagebox.showerror("错误", f"无法打开串口 {port}\n{str(e)}")
    
    def close_serial(self):
        """关闭串口"""
        if self.serial_obj and self.serial_obj.is_open:
            try:
                self.serial_obj.close()
            except Exception as e:
                print(f"关闭串口时出错: {str(e)}")
        
        self.serial_obj = None
        self.is_connected = False
        
        # 更新按钮样式
        self.connect_btn.config(text="打开", bg="#ff4444")
        self.port_entry.config(state=tk.NORMAL)
        
        # 禁用控制按钮
        self.set_buttons_state(False)
        
        self.update_status("串口已断开")
    
    def on_closing(self):
        """关闭窗口时的清理工作"""
        if self.serial_obj and self.serial_obj.is_open:
            try:
                self.serial_obj.close()
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