#power by fengmm521.taobao.com
#wechat:woodmage
import machine
import ujson
import os
import socketUtil

#文件是否存在
def isExists(pth):
    try:
        f = open(pth,'rb')
        f.close()
        return True
    except Exception:
        return False

SSID = None
PASSWORD = None

if SSID is None or PASSWORD is None:
    if not isExists('wifi.json'):
        import webconfig
        webconfig.WebConfig().run() #开始web配网,配网成功后自动保存wifi.json,然后重新启动
    else:
        with open('wifi.json', 'r') as f:
            config = ujson.load(f)
            SSID = config.get('ssid')
            PASSWORD = config.get('password')
            print('wifi config:',SSID,PASSWORD)

import machine
import time
import rtcUtil #需要20260121版本以上固件
import tDriver as t

#实始化一个点击器控制实例对象
tobj = t.TouchObj()
#生成随机整数
def randint(min, max):
    return t.randint(min, max)
#pNumber按键按下,pNumber从1~16
def touchPin(pNumber):
    tobj.setPin(pNumber,False)
    tobj.updateData()
#pNumber按键抬起,pNumber从1~16
def unTouchPin(pNumber):
    tobj.setPin(pNumber,True)
    tobj.updateData()
    
#按下并抬起,即点按一次,pNumber从1~16
def touchOncePin(pNumber):
    #判断输入的点击头编号是否在1~16范围内,不在时程序直接返回,并报错
    if pNumber < 1 or pNumber > 16: 
        print('pin number erro:%d'%(pNumber)) 
        return
    touchPin(pNumber)   #对应点击头按下
    time.sleep_ms(60)   #按下时间为60毫秒,这个时间可以根据需要修改,建议30~100之间
    unTouchPin(pNumber) #对应点击头抬起
    time.sleep_ms(60)   #抬起后再等60毫秒

#使用16位的按键状态数一次控制所有点击头状态
def setAllPinStates(state):
    tobj.set16Pins(state)
    tobj.updateData()
#随机延时min~max毫秒
def randDelayMS(min,max):
    dt = t.randint(min,max)#随机延时min~max毫秒
    time.sleep_ms(dt)

allUntouch = 0b1111111111111111    #所有点击头抬起状态

#使用四个点击头组成一列进行向上滑动操作, 从下向上依次是J1,J2,J3,J4的方式排列
def moveUP():
    tobj.move([1,2,3,4])  #按J1,J2,J3,J4顺序滑动
#向下滑动操作,正好和向上相反
def moveDown():
    tobj.move([4,3,2,1]) #按J4,J3,J2,J1顺序滑动


#慢速双击p号按键后点亮屏幕的操作
def doubleTouch(p):
    touchOncePin(p)
    time.sleep(0.3)
    touchOncePin(p)
#快速双击
def doubleTouchFast(p):
    touchOncePin(p)
    touchOncePin(p)

#长按屏幕,默认是3秒
def longTouch(p,t = 3000):
    touchPin(p)
    time.sleep_ms(t)
    unTouchPin(p)

#判断dat是否为整数字符串
def is_int(dat):
    try:
        int(dat)
        return True
    except:
        return False

## 清除wifi配置,下次上电后,需要重新配置wifi
def cleanWifiConfig():
    os.remove('wifi.json')
    time.sleep_ms(100)
    machine.reset()

def runDAKA():
    print("da ka start")
    touchOncePin(1)      #J1点击一次,打开app
    time.sleep(10)       #延时10秒
    touchOncePin(2)      #J2点击一次,打卡
    time.sleep(10)       #延时10秒
    touchOncePin(3)      #J3点击一次,返回桌面
    time.sleep(5)       #延时5秒

def initConfig():
    pass

def delaytime(n):
    for i in range(n):
        print(n-i)
        time.sleep(1)

runstate = 0

def ontimerEnd(tim):
    global runstate
    if runstate == 0:
        touchPin(16)
    elif runstate == 1:
        touchPin(16)
        touchPin(15)
    elif runstate == 2:
        touchPin(16)
        touchPin(15)
        touchPin(14)
    else:
        unTouchPin(16)
    tkey = tobj.key.value()      #检测物理按键是否被按下,当按键按下时tkey为0,否则为1
    if not tkey:
        runstate += 1
        if runstate > 2:
            runstate = 0
        tim.init(period=1000,mode=machine.Timer.ONE_SHOT ,callback=ontimerEnd)
    else:
        tim.init(period=100,mode=machine.Timer.ONE_SHOT ,callback=ontimerEnd)

lasttouchst = True 
def runonce():
    global lasttouchst
    tmp = 1
    if lasttouchst:
        tmp = 1
    else:
        tmp = 0
    for i in range(9):
        if i%2 == tmp:
            touchOncePin(i)
        time.sleep_ms(100)

def main():
    global lasttouchst,runstate
    print('start wifi')
    wlan = socketUtil.connect_wifi(SSID,PASSWORD)  #让板子连接wifi
    print("\nWiFi connected:", wlan.ifconfig())
    timobj = rtcUtil.RTCUtil()
    timobj.syncRemote() #同步网络时间,同时打印北京时间
    #打卡时间
    lastminute = 0
    wificount = 3600     #wifi时间每小时检查校准一次
    tim1 = machine.Timer(1)    #新建一个物理定时器用来计时
    tim2 = machine.Timer(-99)    #新建一个物理定时器用来计时
    tim2.init(period=1000,mode=machine.Timer.ONE_SHOT ,callback=ontimerEnd)
    lasttouchst = True
    while True:
        year,month,day,hour,minute,second,week = timobj.getBjTimeList()
        print(second)
        touchOncePin(11)
        if minute != lastminute and second == 15:
            lastminute = minute
            print('touch once:%d-%d-%d.%d:%d:%d'%(year,month,day,hour,minute,second))
            if runstate == 0:
                lasttouchst = True
            elif runstate == 1:
                lasttouchst = False
            elif runstate == 2:
                lasttouchst = not lasttouchst
            runonce()
        time.sleep(1) #每秒钟检查一次
        wificount -= 1  #每小时从服务器获取一次时间
        if wificount <= 0:
            wificount = 3600
            if wlan.isconnected(): #wifi连接是否连接
                timobj.syncRemote() #同步网络时间,同时打印北京时间
            else:
                time.sleep_ms(100) #等待100毫秒
                wlan.connect(SSID,PASSWORD)
                print("Connecting to WiFi...", end='')
                connectcount = 30        #wifi连接超时时间30秒
                while not wlan.isconnected():
                    time.sleep(1)
                    connectcount -= 1
                    if connectcount <= 0:
                        print("WiFi connection timeout")
                        break
                if wlan.isconnected():
                    print("\nWiFi connected:", wlan.ifconfig())
                    timobj.syncRemote() #同步网络时间,同时打印北京时间

    #这样获取到时间后,就可以结合出厂程序里的控制点击头的逻辑来用程序控制和时间有关的定时点击操作了
if __name__ == '__main__':
    main()