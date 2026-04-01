#!/usr/bin/python
# -*- coding: utf-8 -*-
#创建SocketServerTCP服务器：
import os
import socket
import time
import platform
from sys import exit
import serial
import serial.tools.list_ports

from sys import version_info

sysSystem = platform.system()

#设置pygame
if sysSystem == 'Windows':  #windows系统
    try:
        import pygame
    except Exception as e:
        print('pygame library installation issue, reconfiguring pygame for Windows...')
        print('Installing pygame locally...')
        cmd = 'python -mpip install pygame-2.0.1-cp37-cp37m-win_amd64.whl'
        os.system(cmd)
        time.sleep(1)
        import pygame
elif sysSystem == 'Darwin': #苹果mac os系统
    try:
        import pygame
    except Exception as e:
        print('pygame library installation issue, reconfiguring pygame for Mac OS...')
        print('Installing pygame locally...')
        cmd = 'python -mpip install pygame-2.0.1-cp37-cp37m-macosx_10_9_intel.whl'
        os.system(cmd)
        time.sleep(1)
        import pygame
elif sysSystem == 'Linux':
    try:
        import pygame
    except Exception as e:
        print('Program does not include pygame for Linux')
        print('Installing pygame from network...')
        cmd = 'python -mpip install pygame'
        os.system(cmd)
        time.sleep(1)
        import pygame

from pygame.locals import *


#获取当前python版本
def pythonVersion():
    return version_info.major


t = None

def readcom():
    global t
    n = t.inWaiting()
    while n<=0:
        time.sleep(0.01)
        n = t.inWaiting()
    pstr = t.read(n)
    if pythonVersion() > 2:
        print(pstr.decode())
    else:
        print(pstr)
    
def sendcmd(cmd):
    global t
    sendstr = cmd
    print(sendstr)
    if pythonVersion() > 2:
        s = t.write(sendstr.encode())
    else:
        s = t.write(sendstr.encode())
    t.flush()

def send(v):
    global t
    sendcmd(v)
    time.sleep(0.03)
    readcom()


BG_IMAGE = 'bg.jpg'
display_width = 500
display_height = 500
BG_Clolor = (0,0,0)
Text_Clolor = (235,190,11)
Select_Color = (100, 200, 100)
Main_screen = None
SELECT_SCREEN = None

#pygame 显示文字
def text_objects(text, font, isClean = False):
    Color = Text_Clolor
    if isClean:
        Color = BG_Clolor
    textSurface = font.render(text, True, Color)
    return textSurface

def text_objects_color(text, font, color):
    textSurface = font.render(text, True, color)
    return textSurface
  
def message_clean(ptype):
    if ptype == 1:
    #清除第一个文字
        pygame.draw.rect(Main_screen, BG_Clolor, (0, display_height/2-55, display_width, 100), 0)
    #清除第二个文字
    else:
        pygame.draw.rect(Main_screen, BG_Clolor, (0, display_height-80, display_width, 100), 0)
    #刷屏
    pygame.display.update()
    time.sleep(0.001)
    
def diaplayKey(text):
    message_clean(1)
    #字体
    TextObj = pygame.font.Font('freesansbold.ttf',80)
    #第一个文字
    TextSurf= text_objects(text, TextObj)
    TextRect = TextSurf.get_rect()
    TextRect.center = ((display_width/2),(display_height/2))
    Main_screen.blit(TextSurf, TextRect)
    pygame.display.update()
    time.sleep(0.01)
    
def diaplayTouchMsg(text):
    message_clean(2)
    #字体
    TextObj = pygame.font.Font('freesansbold.ttf',20)
    #文字
    TextSurf= text_objects(text, TextObj)
    TextRect = TextSurf.get_rect()
    TextRect.center = ((display_width/2),(display_height-50))
    Main_screen.blit(TextSurf, TextRect)
    pygame.display.update()
    time.sleep(0.01)

#定义点击器硬件点击头编号
HardDif = {}

#定义键盘和点击器点击头
keyDownDic = {K_ESCAPE:'esc',K_CAPSLOCK:'cap',K_TAB:'tab',K_SPACE:'space',K_0:'0',K_1:'1',K_2:'2',K_3:'3',K_4:'4',K_5:'5',K_6:'6',K_7:'7',K_8:'8',K_9:'9',K_a:'a',K_b:'b',K_c:'c',K_d:'d',K_e:'e',K_f:'f',K_g:'g',K_h:'h',K_i:'i',K_j:'j',K_k:'k',K_l:'l',K_m:'m',K_n:'n',K_o:'o',K_p:'p',K_q:'q',K_r:'r',K_s:'s',K_t:'t',K_u:'u',K_v:'v',K_w:'w',K_x:'x',K_y:'y',K_z:'z'}

touchState = 0xffff

def hexTocmd(hexdat):
    ttmp = '%x'%(hexdat)
    tdstr = '<' + (4-len(ttmp))*'0' + ttmp + '>'
    return tdstr
    
def printDicData(dicdata):
    for k,v in dicdata.items():
        pstr = 'k:%s,'%(k)
        for i,d in enumerate(v):
            pstr += '%x,'%(d)
        print(pstr)

def initKeyDic():
    f = open('game.ini','r')
    lines = f.readlines()
    f.close()
    for i,v in enumerate(lines):
        v = v.replace('\n','').replace('\r','').replace('\t','').replace(' ','')
        tmps = v.split(':')
        keynum = tmps[0]
        tnum = tmps[1].split(',')
        tdtmp = 0xffff
        tutmp = 0
        for ti,tv in enumerate(tnum):
            ntv = int(tv)
            tutmp = (tutmp | (1<<(ntv-1)))
            tdtmp = (0xffff & (~ tutmp))
        HardDif[keynum] = [tdtmp,tutmp]
    printDicData(HardDif)

def keyDown(kNumber,isHeaveTouch = True):
    global t
    global touchState
    if keyDownDic[kNumber] in HardDif:
        data = HardDif[keyDownDic[kNumber]][0]
        cmddata = ''
        if isHeaveTouch:
            touchState = touchState & data
            cmddata = hexTocmd(touchState)
            sendcmd(cmddata)       #发送点击头按下指令
        else:
            print('Key pressed: %s'%(pygame.key.name(kNumber)))
        diaplayTouchMsg("J%s touch down, send->'%s'"%(keyDownDic[kNumber],cmddata))
    else:
        print('Key down: %s not in config file'%(keyDownDic[kNumber]))

def keyUp(kNumber,isHeaveTouch = True):
    global t
    global touchState
    if keyDownDic[kNumber] in HardDif:
        data = HardDif[keyDownDic[kNumber]][1]
        cmddata = ''
        if isHeaveTouch:
            touchState = touchState | data
            cmddata = hexTocmd(touchState)
            sendcmd(cmddata)       #发送点击头弹起指令      
        else:
            print('Key released: %s'%(pygame.key.name(kNumber)))
        diaplayTouchMsg("J%s touch up, send->'%s'"%(keyDownDic[kNumber],cmddata))
    else:
        print('Key up: %s not in config file'%(keyDownDic[kNumber]))
        
def readconfig():
    try:
        f= open('com.ini')
        jstr = f.read()
        f.close()
        comstr = 'com'+jstr
        if sysSystem == 'Darwin':
            comstr = jstr
        return comstr
    except:
        return None

def saveconfig(comport):
    f = open('com.ini', 'w')
    if sysSystem == 'Windows':
        f.write(comport.replace('com', ''))
    else:
        f.write(comport)
    f.close()

def get_available_ports_with_info():
    """Get all available serial ports with description"""
    ports = serial.tools.list_ports.comports()
    port_info_list = []
    for port in ports:
        # Get port name and description
        port_name = port.device
        port_desc = port.description
        
        # Clean up description for display
        if port_desc:
            # Remove duplicate port name from description if present
            if port_name in port_desc:
                port_desc = port_desc.replace(port_name, '').strip()
            # Truncate long descriptions
            if len(port_desc) > 40:
                port_desc = port_desc[:37] + '...'
        else:
            port_desc = "No description"
            
        port_info_list.append({
            'name': port_name,
            'description': port_desc,
            'full_info': f"{port_name} - {port_desc}" if port_desc else port_name
        })
    return port_info_list

def select_serial_port():
    """Serial port selection interface with descriptions"""
    global SELECT_SCREEN
    
    # Get available ports with info
    port_info_list = get_available_ports_with_info()
    
    if not port_info_list:
        print("No available serial ports found!")
        return None
    
    # Create selection interface
    pygame.init()
    select_width = 600
    select_height = 400
    SELECT_SCREEN = pygame.display.set_mode((select_width, select_height))
    pygame.display.set_caption("Select Serial Port")
    SELECT_SCREEN.fill(BG_Clolor)
    
    # Font settings
    title_font = pygame.font.Font('freesansbold.ttf', 32)
    port_font = pygame.font.Font('freesansbold.ttf', 20)
    desc_font = pygame.font.Font('freesansbold.ttf', 16)
    hint_font = pygame.font.Font('freesansbold.ttf', 14)
    
    # Title
    title_text = title_font.render("Select Serial Port", True, Text_Clolor)
    title_rect = title_text.get_rect(center=(select_width/2, 30))
    SELECT_SCREEN.blit(title_text, title_rect)
    
    # Display port list
    selected_index = 0
    scroll_offset = 0
    max_display = 10  # Display up to 10 ports
    
    clock = pygame.time.Clock()
    running = True
    
    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                exit()
            elif event.type == KEYDOWN:
                if event.key == K_UP:
                    selected_index = max(0, selected_index - 1)
                    # Handle scrolling
                    if selected_index < scroll_offset:
                        scroll_offset = selected_index
                elif event.key == K_DOWN:
                    selected_index = min(len(port_info_list) - 1, selected_index + 1)
                    # Handle scrolling
                    if selected_index >= scroll_offset + max_display:
                        scroll_offset = selected_index - max_display + 1
                elif event.key == K_RETURN or event.key == K_SPACE:
                    # Confirm selection
                    selected_port = port_info_list[selected_index]['name']
                    pygame.quit()
                    return selected_port
                elif event.key == K_ESCAPE:
                    # Exit
                    pygame.quit()
                    exit()
            elif event.type == MOUSEBUTTONDOWN:
                # Mouse click selection
                if event.button == 1:  # Left button
                    x, y = event.pos
                    if 80 <= y <= 80 + len(port_info_list) * 50:
                        index = (y - 80) // 50 + scroll_offset
                        if 0 <= index < len(port_info_list):
                            selected_index = index
        
        # Draw background
        SELECT_SCREEN.fill(BG_Clolor)
        SELECT_SCREEN.blit(title_text, title_rect)
        
        # Draw port list
        start_y = 80
        item_height = 50
        for i in range(scroll_offset, min(scroll_offset + max_display, len(port_info_list))):
            port_info = port_info_list[i]
            y_pos = start_y + (i - scroll_offset) * item_height
            
            # Add background highlight for selected item
            if i == selected_index:
                pygame.draw.rect(SELECT_SCREEN, (50, 50, 50), 
                               (20, y_pos, select_width - 40, item_height - 2))
            
            # Draw port name (bold)
            port_name_text = port_font.render(port_info['name'], True, 
                                             Select_Color if i == selected_index else Text_Clolor)
            SELECT_SCREEN.blit(port_name_text, (30, y_pos + 5))
            
            # Draw description (smaller font, lighter color)
            if port_info['description']:
                desc_color = (150, 150, 150) if i != selected_index else (200, 200, 200)
                desc_text = desc_font.render(port_info['description'], True, desc_color)
                SELECT_SCREEN.blit(desc_text, (30, y_pos + 30))
        
        # Draw separator line
        pygame.draw.line(SELECT_SCREEN, (100, 100, 100), (20, start_y - 5), (select_width - 20, start_y - 5), 1)
        
        # Display hint
        hint_text = hint_font.render("UP/DOWN Select | ENTER Confirm | ESC Exit", True, Text_Clolor)
        hint_rect = hint_text.get_rect(center=(select_width/2, select_height - 40))
        SELECT_SCREEN.blit(hint_text, hint_rect)
        
        # Display count info
        count_text = hint_font.render(f"Total: {len(port_info_list)} port(s)", True, Text_Clolor)
        count_rect = count_text.get_rect(center=(select_width/2, select_height - 20))
        SELECT_SCREEN.blit(count_text, count_rect)
        
        pygame.display.update()
        clock.tick(30)

def main(isHeaveTouch = True):
    global t
    global Main_screen
    
    # Initialize key configuration
    initKeyDic()
    
    # Get baud rate
    btv = 115200
    
    # Select serial port
    print("Detecting available serial ports...")
    port_info_list = get_available_ports_with_info()
    available_ports = [port['name'] for port in port_info_list]
    
    if not available_ports:
        print("Error: No available serial ports found!")
        print("Please check if serial device is connected.")
        input("Press Enter to exit...")
        return
    
    print(f"Found {len(available_ports)} port(s):")
    for i, port_info in enumerate(port_info_list):
        print(f"  {i+1}. {port_info['name']} - {port_info['description']}")
    
    # Try to read previously used port from config file
    saved_port = readconfig()
    
    if saved_port and saved_port in available_ports:
        print(f"Previously used port: {saved_port}")
        # Use the saved port directly
        dev = saved_port
        print(f"Connecting to {dev}...")
    else:
        # Show selection interface
        print("\nPlease select a port from the window...")
        dev = select_serial_port()
        if not dev:
            print("No port selected, exiting program.")
            return
    
    # Try to connect to serial port
    try:
        t = serial.Serial(dev, btv, timeout=1)
        print(f"Successfully connected to {dev} (Baud rate: {btv})")
        # Save configuration
        saveconfig(dev)
    except Exception as e:
        print(f"Failed to connect to serial port: {e}")
        # If auto-connect fails, try manual selection
        print("\nPlease select port manually...")
        dev = select_serial_port()
        if dev:
            try:
                t = serial.Serial(dev, btv, timeout=1)
                print(f"Successfully connected to {dev} (Baud rate: {btv})")
                saveconfig(dev)
            except Exception as e2:
                print(f"Failed to connect to serial port: {e2}")
                input("Press Enter to exit...")
                return
        else:
            print("No port selected, exiting program.")
            return
    
    if t:
        pygame.init()
        Main_screen = pygame.display.set_mode((display_width, display_height), 0, 32)
        pygame.display.set_caption("Keyboard to Touchpad")
        Main_screen.fill((0, 0, 0))
        pygame.display.update()
        
        # Show connection success message
        diaplayTouchMsg(f"Connected to {dev}")
        time.sleep(1)
        
        while 1:
            for event in pygame.event.get():
                if event.type == QUIT:
                    exit()
                elif event.type == KEYDOWN:
                    print('KEYDOWN')
                    diaplayKey('%s Down'%(pygame.key.name(event.key)))
                    if event.key in keyDownDic:
                        keyDown(event.key,isHeaveTouch)
                    elif event.key == K_ESCAPE:
                        exit()
                    else:
                        print('Key pressed, but %s not bound to touchpad'%(pygame.key.name(event.key)))
                        message_clean(2)
                    
                elif event.type == KEYUP:
                    print('KEYUP')
                    diaplayKey('%s Up'%(pygame.key.name(event.key)))
                    if event.key in keyDownDic:
                        keyUp(event.key,isHeaveTouch)
                    else:
                        print('Key released, but %s not bound to touchpad'%(pygame.key.name(event.key)))
                        message_clean(2)
                elif event.type == MOUSEMOTION:
                    pass
    else:
        print('Init serial error...')

if __name__ == '__main__':
    main()