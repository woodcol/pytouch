from subprocess import Popen, TimeoutExpired, PIPE , STDOUT
import os,sys
import time
import platform
import threading
from pygame import mixer  # 用于播放音频
import serial
import shutil
import serial.tools.list_ports
import asyncio
from bleak import BleakScanner
import pathtool
import deviceCheck

sysSystem = platform.system()


env = os.environ.copy()
env['PYTHONIOENCODING'] = 'utf-8'

wd = os.getcwd()
os.chdir(".")

ESPTOOL = 'esptool.exe'
ampytool = 'ampy'

serialName = 'USB-SERIAL CH340'

if sysSystem == 'Darwin' or sysSystem == 'Linux':
    serialName = 'USB Serial'
    ESPTOOL = 'esptool.py'

logtxt = ''

def saveLog(data):
    f = open('log.txt','w')
    f.write(logtxt)
    f.close()

def play_audio(filename):
    mixer.init()  # 初始化pygame混音器
    mixer.music.load(filename)
    mixer.music.play()
    while mixer.music.get_busy():  # 等待音乐播放完毕
        continue

def playOK():
    play_audio('ok.mp3')

def playErro():
    play_audio('erro.mp3')

def listComPorts():
    ports_list = list(serial.tools.list_ports.comports())
    outs = []
    if len(ports_list) <= 0:
        print("无串口设备。")
    else:
        # print("可用的串口设备如下：")
        for comport in ports_list:
            # print(list(comport)[0], list(comport)[1])
            outs.append([list(comport)[0],list(comport)[1]])
    return outs

def chickPortName(pname = serialName,isSmall = True):
    plist = listComPorts()
    ports = []
    for i, v in enumerate(plist):
        if v[1].find(pname) != -1:
            # print(v[0])
            ports.append(v[0])
    if len(ports) > 0:
        # print('find %d ports:' % len(ports))
        # print(ports)
        outs = []
        for idx, port in enumerate(ports):
            outs.append(int(port[3:]))
        if isSmall:
            outs.sort()
        else:
            outs.sort(reverse=True)
        return outs
    return None

def fandBinName():
    bins = pathtool.getAllExtFile('..','.bin',0)
    # print(bins[0])
    return bins[0][2] + '.bin'
def runCMDAndOUT(cmd, code="latin1"):
    global logtxt
    print(cmd)
    process = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, env=env)
    while process.poll() is None:
        line = process.stdout.readline()
        line = line.decode(code).strip()  # 使用指定的编码解码行
        if line:
            print(line)
            logtxt += line + '\n'

def uploadEbin(comport):
    #烧写加密后的flash固件
    if not comport:
        print('not find com port')
        return
    binname = fandBinName()
    cmd = ESPTOOL + ' --chip esp8266 -p %s --baud 115200 write_flash --flash_size=detect 0 ../%s'%(comport,binname)
    runCMDAndOUT(cmd)

def resetDevice(comport):
    cmd = ESPTOOL + ' -p %s run'%(comport)
    runCMDAndOUT(cmd)



def eraseFlash(comport):
    cmd = ESPTOOL + ' -p %s erase_flash'%(comport)
    runCMDAndOUT(cmd)

def delaytime(ns,port = None):
    count = ns
    for i in range(ns):
        print('delay %d s-->port:%d'%(count,port))
        time.sleep(1)
        count -= 1

def chickPort(n):
    cstr = 'COM' + str(n)
    plist = listComPorts()
    for i,v in enumerate(plist):
        if v[0] == cstr:
            print('find Port COM%d:'%(n),v)
            return True
    print('not find COM%d'%(n))
    return False

def getCH340PortNumAll():
    ports = chickPortName()
    return ports

def saveErroCom(comport):
    with open('erro.txt','a') as f:
        f.write(comport + '\n')

def checkBoardOK(comport):
    deviceCheck.oprnSerial(comport)
    if deviceCheck.checkBoard():
        deviceCheck.showOK()
        playOK()
    else:
        playErro()
    

def checkBleWithCom(comport):
    serialpt = serial.Serial(comport,115200,timeout=1)
    if serialpt:
        print(serialpt.name)               #串口名
        print(serialpt.port)               #串口号
        print(serialpt.baudrate)           #波特率
        print(serialpt.bytesize)           #字节大小
        print(serialpt.parity)             #校验位N－无校验，E－偶校验，O－奇校验
        print(serialpt.stopbits)           #停止位
        print(serialpt.timeout)            #读超时设置
        print(serialpt.writeTimeout)       #写超时
        print(serialpt.xonxoff)            #软件流控
        print(serialpt.rtscts)             #硬件流控
        print(serialpt.dsrdtr)             #硬件流控
        print(serialpt.interCharTimeout)   #字符间隔超时
        print('-'*10)
        serialpt.setDTR(False)
        time.sleep(0.5)
        serialpt.setDTR(True)
        time.sleep(0.5)
        serialpt.write(b'0x03')
        serialpt.flush()
        time.sleep(1)
        n = serialpt.inWaiting()
        if n:
            pstr = serialpt.read(n)
            print(str(pstr))
        serialpt.write(b'0x04')
        serialpt.flush()
        time.sleep(0.3)
        n = serialpt.inWaiting()
        if n:
            pstr = serialpt.read(n)
            print(str(pstr))
        while True:
            n = serialpt.inWaiting()
            while n<=0:
                time.sleep(0.002)
                n = serialpt.inWaiting()
            pstr = serialpt.read(n)
            print(str(pstr))
            if pstr.find(b'ble guangbo') != -1:
                break
        serialpt.write('test\n'.encode('utf-8'))
        serialpt.flush()
        time.sleep(3)
        n = serialpt.inWaiting()
        res = ''
        if n:
            res = serialpt.read(n).decode('utf-8')
            if n < 5:
                time.sleep(0.01)
                n = serialpt.inWaiting()
                if n:
                    res += serialpt.read(n).decode('utf-8')
        if res.find('bleok') != -1:
            print('burn success')
            return True
        else:
            print('burn fail')
            return False
        
def resetDeviceCom(comport):
    serialpt = serial.Serial(comport,115200,timeout=1)
    if serialpt:
        print(serialpt.name)               #串口名
        print(serialpt.port)               #串口号
        print(serialpt.baudrate)           #波特率
        print(serialpt.bytesize)           #字节大小
        print(serialpt.parity)             #校验位N－无校验，E－偶校验，O－奇校验
        print(serialpt.stopbits)           #停止位
        print(serialpt.timeout)            #读超时设置
        print(serialpt.writeTimeout)       #写超时
        print(serialpt.xonxoff)            #软件流控
        print(serialpt.rtscts)             #硬件流控
        print(serialpt.dsrdtr)             #硬件流控
        print(serialpt.interCharTimeout)   #字符间隔超时
        print('-'*10)
        serialpt.setDTR(False)
        time.sleep(0.5)
        serialpt.setDTR(True)
        time.sleep(0.5)
        serialpt.write(b'0x03')
        serialpt.flush()
        time.sleep(1)
        n = serialpt.inWaiting()
        if n:
            pstr = serialpt.read(n)
            print(str(pstr))
        serialpt.write(b'0x04')
        serialpt.flush()
        time.sleep(0.3)
        st = time.time()
        while True:
            n = serialpt.inWaiting()
            while n<=0:
                time.sleep(0.002)
                n = serialpt.inWaiting()
            pstr = serialpt.read(n)
            print(str(pstr))
            dt = time.time() - st
            if dt > 5:
                break
def burnDevice(port):
    strport = 'COM' + str(port)
    eraseFlash(strport)
    delaytime(1,port)
    uploadEbin(strport)
    delaytime(3,port)
    resetDevice(strport)
    delaytime(3,port)
    checkBoardOK(strport)

portdict = {}
threaddict = {}
lock = threading.Lock()

def runAutoBurn(port):
    global portdict
    while True:
        if chickPort(port):
            lock.acquire() #获取锁
            portflog = portdict.get(port)
            lock.release() #释放锁
            if portflog == False:
                delaytime(1,port)
                lock.acquire() #获取锁
                portdict[port] = True
                lock.release() #释放锁
                burnDevice(port)
            else:
                time.sleep(3)
                print('port:com%d is bren ok,please change board ...'%(port))
        else:
            lock.acquire() #获取锁
            portdict[port] = False
            lock.release() #释放锁
            time.sleep(3)
            
def main():
    global portdict
    while True:
        pts = getCH340PortNumAll()
        if not pts:
            print('no device found,please check the device ...')
            time.sleep(3)
            continue
        for i,v in enumerate(pts):
            if v in portdict.keys():
                continue
            else:
                portdict[v] = False
        for k,v in portdict.items():
            if k in threaddict.keys():
                continue
            else:
                delaytime(3,k)
                threaddict[k] = threading.Thread(target=runAutoBurn,args=(k,))
                threaddict[k].setDaemon(True)
                threaddict[k].start()
                print('port:com%d thread is start ...')
        time.sleep(3)

def test():
    # blename = 'name.txt'
    # bledir = 'blename/6'
    # # if not os.path.exists(bledir):
    # #     print('not exist %s,make it'%(bledir))
    # # os.getcwd()
    # # print(os.getcwd() + os.sep + bledir)
    # # os.makedirs(os.getcwd() + os.sep + bledir)
    # # else:
    # #     print('exist %s'%(bledir))
    # # with open(bledir + os.sep + blename,'w') as f:
    # #     f.write('fengmm521_%s'%('COM6'))
    # checkBleWithCom('com6')
    # binname = fandBinName()
    # print(binname)
    import os
    fpth = pathtool.GetParentPath()
    print(os.getcwd())
    print('fpth:', fpth)


if __name__ == '__main__':
    args = sys.argv
    if len(args) >= 2:
        print('test')
        test()
    else:
        main()
