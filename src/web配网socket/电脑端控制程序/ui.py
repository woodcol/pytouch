import tkinter as tk
from tkinter import messagebox
import socket
import json
import os

PORT = 23
CONFIG_FILE = "config.json"

client_socket = None

# ====== 記憶IP ======
def load_ip():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
            return data.get("ip", "")
    return ""

def save_ip(ip):
    with open(CONFIG_FILE, "w") as f:
        json.dump({"ip": ip}, f)

# ====== Socket 連線 ======
def connectNet(ip):
    global client_socket
    client_socket = socket.socket()
    client_socket.connect((ip, PORT))

# ====== GUI 控制 ======
def connect():
    ip = ip_entry.get().strip()
    if not ip:
        messagebox.showwarning("提示", "請輸入IP地址")
        return

    try:
        connectNet(ip)
        save_ip(ip)  # ✅ 記住IP
        messagebox.showinfo("提示", f"連線成功: {ip}")
    except Exception as e:
        messagebox.showerror("錯誤", str(e))

def set_mode_at():
    client_socket.send('@'.encode())

def set_mode_ex():
    client_socket.send('!'.encode())

def press_key(pin):
    client_socket.send(type2Pins[pin][0].encode())

def release_key(pin):
    client_socket.send(type2Pins[pin][1].encode())

def click_once(pin):
    client_socket.send(type1Pins[pin].encode())

# ====== 你的字典 ======
type1Pins = {1:'1',2:'2',3:'3',4:'4',5:'5',6:'6',7:'7',8:'8',9:'9',10:'a',11:'b',12:'c',13:'d',14:'e',15:'f',16:'g'}

type2Pins = {
    1:['0','1'],2:['2','3'],3:['4','5'],4:['6','7'],
    5:['8','9'],6:['a','b'],7:['c','d'],8:['e','f'],
    9:['g','h'],10:['i','j'],11:['k','l'],12:['m','n'],
    13:['o','p'],14:['q','r'],15:['s','t'],16:['u','v']
}

# ====== 建立視窗 ======
root = tk.Tk()
root.title("16路點擊頭控制面板")
root.geometry("520x650")

# ====== IP 輸入區 ======
frame_ip = tk.Frame(root)
frame_ip.pack(pady=10)

tk.Label(frame_ip, text="IP地址:").grid(row=0, column=0)

ip_entry = tk.Entry(frame_ip, width=20)
ip_entry.grid(row=0, column=1, padx=5)

# 載入記憶IP
ip_entry.insert(0, load_ip())

tk.Button(frame_ip, text="連線", command=connect).grid(row=0, column=2, padx=5)

# ====== 模式切換 ======
frame_top = tk.Frame(root)
frame_top.pack(pady=10)

tk.Button(frame_top, text="@模式", width=10, command=set_mode_at).grid(row=0, column=0, padx=5)
tk.Button(frame_top, text="!模式", width=10, command=set_mode_ex).grid(row=0, column=1, padx=5)

# ====== 16個按鍵 ======
frame_keys = tk.Frame(root)
frame_keys.pack()

for i in range(16):
    pin = i + 1
    row = i // 4
    col = i % 4

    frame = tk.Frame(frame_keys, relief="ridge", borderwidth=2)
    frame.grid(row=row, column=col, padx=5, pady=5)

    tk.Label(frame, text=f"PIN {pin}").pack()

    tk.Button(frame, text="按下",
              command=lambda p=pin: press_key(p),
              width=8).pack()

    tk.Button(frame, text="放開",
              command=lambda p=pin: release_key(p),
              width=8).pack()

    tk.Button(frame, text="點一下(!)",
              command=lambda p=pin: click_once(p),
              width=8).pack()

# ====== 啟動 ======
root.mainloop()