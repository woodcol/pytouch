#power by fengmm521.taobao.com
#wechat:woodmage
import tDriver as t
import time
from machine import ADC
import uartUtil

# 初始化ADC（ESP8266只有一个ADC引脚，连接到TOUT引脚）
adc = ADC(0)  # 创建ADC对象，参数0表示ADC引脚

#实始化一个点击器控制实例对象
tobj = t.TouchObj()
#生成随机整数
def randint(min, max):
    return t.randint(min, max)
#pNumber按键按下,pNumber从1~16
def touchPin(pNumber):
    tobj.setPin(pNumber,True)
    tobj.updateData()
#pNumber按键抬起,pNumber从1~16
def unTouchPin(pNumber):
    tobj.setPin(pNumber,False)
    tobj.updateData()
#按下并抬起,即点按一次,pNumber从1~16
def touchOncePin(pNumber):
    #判断输入的点击头编号是否在1~16范围内,不在时程序直接返回,并报错
    if pNumber < 1 or pNumber > 16: 
        print('pin number erro:%d'%(pNumber)) 
        return
    touchPin(pNumber)   #对应点击头按下
    time.sleep_ms(80)   #按下时间为80毫秒,这个时间可以根据需要修改,建议30~100之间
    unTouchPin(pNumber) #对应点击头抬起
    time.sleep_ms(80)   #抬起后再等80毫秒

#使用四个点击头组成一列进行向上滑动操作, 从下向上依次是J1,J2,J3,J4的方式排列
def moveUP():
    tobj.move([1,2,3,4])  #按J1,J2,J3,J4顺序滑动
#向下滑动操作,正好和向上相反
def moveDown():
    tobj.move([4,3,2,1]) #按J4,J3,J2,J1顺序滑动

#使用16位的按键状态数一次控制所有点击头状态
def setAllPinStates(state):
    tobj.set16Pins(state)
    tobj.updateData()

allUntouch = 0b1111111111111111    #所有点击头抬起状态
danshu     = 0b1010101010101010    #单数按下状态
shuanshu   = 0b0101010101010101    #双数按下状态

isRUN = False                      #定义程序运行控制全局变量

isSetData = False #是否是设置ACD参数
mutildat = ''

adcConfig = 500

isShowADC = True

def setADCData():
    global adcConfig
    if len(mutildat) > 0:
        try:
            adcConfig = int(mutildat.strip())
            print('adc config is:',adcConfig)
        except Exception:
            adcConfig = 300
            print('set adc config fomart error')
    else:
        print('set adc config data empty')
    with open('config.txt','w') as f:
        f.write(str(adcConfig))
def getADCData():
    global adcConfig
    try:
        with open('config.txt','r') as f:
            adcConfig = int(f.read().strip())
            print('adc config is:',adcConfig)
    except Exception:
        adcConfig = 300
        print('not config.txt file,set default:300')

def uartCheck():
    global isShowADC,isSetData,mutildat
    dat = uartUtil.reciveDat(True) #True表示每次只接收一个字节数据,只要有数据就一直接收,默认是False,接收一行数据,只有以换行符结束才会返回
    if dat: #接收到数据,dat将不为None
        # print('recive uart data:%s'%(dat.decode())) #decode是把字节流数据转成字符串格式
        dat = dat.decode().strip() #strip()是去掉字符串两边的空格
        # print(len(dat),dat)
        if dat == '[':
            isSetData = True
        elif dat == ']':
            isSetData = False
            setADCData()
        elif isSetData and (dat >= '0' and dat <= '9'):
            mutildat += dat
        elif dat == '0':
            print(dat)
            isShowADC = False
        elif dat == '1':
            isShowADC = True
            print(dat)
        else:
            print('error data:%s'%(dat))

def checkADC():
    """读取原始ADC值并转换为电压"""
    # 读取原始值（0-1023）
    raw_value = adc.read()
    if isShowADC:
        print(raw_value)
    if raw_value < adcConfig:
        return True
    else:
        return False

def openSwitch(n):
    touchPin(n)
def closeSwitch(n):
    unTouchPin(n)

    
#主函数,点击器程序从这里开始运行
def main():
    global isRUN                     #引用全局变量isRUN
    setAllPinStates(0)      #初始化所有点击头为抬起状态
    index = 0
    lastKey = True
    ptime = time.time()             #记录当前时间

    while True:
        tkey = tobj.key.value()      #检测物理按键是否被按下,当按键按下时tkey为0,否则为1
        if not tkey:                 #按键是按下状态
            if lastKey:              #上一个状态是抬起
                index += 1           #开关编号+1
                if index > 16:       #开关编号>16时，把编号改成0
                    index = 1
                openSwitch(index)    #打开对应编号开关
                lastKey = False      #设置当前按键按下
                ptime = time.time()             #记录当前时间
            else:
                if time.time() - ptime >=6: #按键按下时间超过10秒
                     setAllPinStates(0xFFFF) #打开所有开关
        else:                        #按键状态是抬起
            if not lastKey:          #按键上次状态是按下，说明按键状态改变
                # closeSwitch(n)       #关闭对应编号按键
                setAllPinStates(0)   #关闭所有开关
                lastKey = True       #设置当前是抬起
        time.sleep_ms(100)           #延时10ms
        uartCheck()
        checkADC()
        
        

if __name__ == '__main__':  
    main()
