#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
[about]
    :adaptation     =>  timmy (WeiWen Wu)
    :date                   =>  2022/11/21
    :version             =>  2.0  (for python3 )
[pkg]
    :serial (pyseial)
    :time
    :multiprocessing、threading
    :(pyfirmata2)
[tutorial]
    :G-code            =>  https://kknews.cc/zh-tw/tech/39k2xx3.html
    :pyseial            =>  https://pyserial.readthedocs.io/en/latest/pyserial_api.html
"""
import serial
from  time import sleep

class setting:
    ### serial_port ###
    serial_port_auto = True
    serial_port_auto_get_count = 10

    ### AR3 ###
    # speed = 200
    realtime = False
    
    joint_angle_limit = [300,90,135,200,180,300]
    standard_posture = [240,30,30,85,165,155]
    # setting.standard_posture = [155,0,17,85,145,155]
    
    join_count = 6

    ### message ###
    warning = False
    set_one_absolute_info = True



class AR3:
    """
    [use]
        :arm = AR3("/dev/ttyUSB3")

        :arm.set_all([0,0,0,0,0,0])
        :ar3.set_all([90,90,90,90,90,90])
        :print(arm.get_all())

        :arm.close()

    [search  serial  port]
        :dmesg | grep tty
    """
    servo_angle = -1
    speed = 2000
    standard_posture = [240,30,30,85,165,155]
    # setting.standard_posture = [155,0,17,85,145,155]
    def __init__(self,__serial_port=""):
        if setting.serial_port_auto ==True:
            self._serial_port = serial_port().auto_get()
        elif setting.serial_port_auto ==False and  __serial_port == "":
            raise ValueError("Please enter <serial_port> because <serial_port_auto> = True")
        else:
            self._serial_port = __serial_port

        ### setting speed ###
        try:
            self.ARM=serial.Serial(self._serial_port,115200,timeout=0.5)
            # self.set_speed(setting.speed) 
        except Exception as e:
            print("\033[1;31mNot connect to arm => dmesg | grep tty")
            print("\033[0;31m"+str(e))
            exit() 

        ### Multithreading (多線程) ###
        if setting.realtime == True:
            import multiprocessing
            import threading
            # self.show_angel_rt=multiprocessing.Process(target=self.__show_angel_realtime)
            self.show_angel_rt=threading.Thread(target=self.__show_angel_realtime)
            self.show_angel_rt.start()

        self.ARM_joint = ["X","Y","Z","A","B","C",""]   # 關節代碼[0~5 , 全部]

    def data_pub(self,data):                                       
        """ 發布訊息 """
        while self.ARM.isOpen() == False:
            print("\033[1;33m[wait] wait  serial port open\033[0m")
            self.ARM.open()
        data = data+"\r\n"
        self.ARM.write(data.encode())            
       

    def serial_test(self):
        """ dmesg | grep tty """ 
        __temp = ""
        try:
            self.data_pub("?")
            data = self.ARM.readline()     
            if "<Idle|MPos:" in data: 
                __temp =  data
            else:
                __temp =  "False(find serial port,but not the arm)\ndata => " + data
            self.ARM.close()
            return __temp
        except Exception as e:
            return "False(serial port not found)\nerror => " + str(e)

    def set_one_relative(self,ARM_joint_num,angle): # G91 相對定位
        """設定 單一關節 之 相對角度"""
        self.data_pub("$J=G91"+self.ARM_joint[ARM_joint_num] + str(angle))  

    def set_one_absolute(self,ARM_joint_num,absolute_angle): # G90 絕對定位
        """設定 單一關節 之 絕對角度"""
        if ARM_joint_num > (setting.join_count+1) or ARM_joint_num< 0:
            raise  ValueError("<ARM_joint_num>  value is 0 to 5 (The current value is  %s ) , in set_one_absolute" % (ARM_joint_num))
        if absolute_angle > setting.joint_angle_limit[ARM_joint_num]:
            raise  ValueError("The %s axis angle exceeds the limit (%s) , in set_one_absolute" % (ARM_joint_num,setting.joint_angle_limit[ARM_joint_num]))
        
        self.data_pub("$J=G90"+self.ARM_joint[ARM_joint_num] + str(absolute_angle)) 

        self.ARM.flush()
        self.ARM.flushInput()

        # while not  float(self.get_one(ARM_joint_num)) > (absolute_angle-0.1) and float(self.get_one(ARM_joint_num)) < (absolute_angle+0.1):
        #     if setting.set_one_absolute_info == True:
        #         print("[wait] joint%s => %s" % (ARM_joint_num,self.get_one(ARM_joint_num)))
        #     pass

        if setting.set_one_absolute_info == True:
            print("[ok] joint%s => %s" % (ARM_joint_num,self.get_one(ARM_joint_num)))

    def set_all_relative(self,absolute_angle_list):
        """設定 全部關節(6個) 之 絕對角度"""
        for n in range(0,setting.join_count-1):
                if (absolute_angle_list[n]+float(self.get_one(n))) >= setting.joint_angle_limit[n]:
                    raise ValueError("The %s axis angle exceeds the limit (%s) , in set_one_absolute" % (n,setting.joint_angle_limit[n]))

        if len(absolute_angle_list) == setting.join_count:
            self.data_pub("$J=G91X%sY%sZ%sA%sB%sC%sF%s"%(absolute_angle_list[0],absolute_angle_list[1],absolute_angle_list[2],absolute_angle_list[3],absolute_angle_list[4],absolute_angle_list[5],setting.speed))  
        else:
            raise ValueError("<absolute_angle_lists>  must have 6 values")

        now_angle=0
        while not  now_angle > [a-0.1 for a in list(map(float,self.get_all()))] and now_angle < [a+0.1 for a in list(map(float,self.get_all()))]:
            now_angle =  list(map(float,self.get_all()))
            pass

    def set_all_absolute(self,absolute_angle_list):
        """設定 全部關節(6個) 之 絕對角度"""
        def check():
            for n in range(0,setting.join_count-1):
                if absolute_angle_list[n] >= setting.joint_angle_limit[n]:
                    raise ValueError("The %s axis angle exceeds the limit (%s) , in set_one_absolute" % (n,setting.joint_angle_limit[n]))

        # def c():
        #     now_angle= list(map(float,self.get_all()))
        #     for n in range(0,6):
        #         if  not now_angle[n] > absolute_angle_list[n] -0.1  and now_angle[n] < absolute_angle_list[n] +0.1 :
        #             return False
        #     return True

        if len(absolute_angle_list) == 6:
            check()
            print("\033[1;32m[start(absolute)] \033[0m%s" % (absolute_angle_list))
            self.data_pub("$J=G90X%sY%sZ%sA%sB%sC%sF%s"%(absolute_angle_list[0],absolute_angle_list[1],absolute_angle_list[2],absolute_angle_list[3],absolute_angle_list[4],absolute_angle_list[5],self.speed))  
            
        elif len(absolute_angle_list) == 7:
            check()
            print("\033[1;32m[start(absolute,servo)]\033[0m %s" % (absolute_angle_list))
            self.servo(absolute_angle_list[6])
            self.data_pub("$J=G90X%sY%sZ%sA%sB%sC%sF%s"%(absolute_angle_list[0],absolute_angle_list[1],absolute_angle_list[2],absolute_angle_list[3],absolute_angle_list[4],absolute_angle_list[5],self.speed)) 
        
        elif len(absolute_angle_list) == 2:
            sleep(absolute_angle_list[1])
            self.servo(absolute_angle_list[0])
            # self.servo(absolute_angle_list[0])
            print("\033[1;32m[start(servo)] \033[0m%s" % (absolute_angle_list))
            # sleep(5)
            self.ARM.flush()
            return
        else:
            raise ValueError("<absolute_angle_lists>  must have 2,6,7 values")
        
        ### ###
        # while  c() == False:
        #     print(c())
        #     pass

        now_angle= list(map(float,self.get_all()))
        while not  now_angle > [a-0.1 for a in absolute_angle_list[0:6]] and now_angle < [a+0.1 for a in absolute_angle_list[0:6]]:
            now_angle =  list(map(float,self.get_all()))
            # print("wait")
            pass

        self.ARM.flush()

    def servo(self,servo_angle):
        """設定 伺服馬達 角度 ( 0 ~ 60 )"""
        if servo_angle < 0 or servo_angle > 60:
            raise ValueError("<servo_angle>  value is 0 to 60 (The current value is  %s ) , in servo" % (servo_angle))
        self.data_pub("Q"+str(servo_angle+2000))   # 2 ; 1 => 1000
        self.servo_angle = servo_angle

    def run_way(self,*absolute_angle_lists):
        """沿 路徑 執行"""
        for absolute_angle_list in absolute_angle_lists:
            # self.restart()
            self.set_all_absolute(absolute_angle_list)
            # if len(absolute_angle_list ) == 6:
            #     self.set_all_absolute(absolute_angle_list)
            #     # sleep(setting.run_way_delay)
            # else:
            #     raise ValueError("<absolute_angle_lists>  must have 6 values , in run_way")

    def get_one(self,ARM_joint_num):
        """取得 單一關節 之 角度"""
        if ARM_joint_num > 5 or ARM_joint_num< 0:
            raise  ValueError("<ARM_joint_num>  value is 0 to 5 (The current value is  %s ) , in ARM_joint_num" % (ARM_joint_num))
        return self.get_all()[ARM_joint_num]
   
    def get_all(self):
        """取得 全部關節(6個) 之 角度"""
        data = []
        while len(data ) != 8: 
            # self.restart()
            sleep(0.5)
            self.data_pub("?")
            data =  self.ARM.readline().decode()
            data_start = data.find(":") + 1         
            data_END = data.find("|",data_start)   
            data = data[data_start:data_END].split(',')
            self.ARM.flush()
            self.ARM.flushInput()
            if setting.warning == True : print("\033[33m[warning] %s , in get_all\033[0m" % (data))
        return data[0:setting.join_count]

    def __show_angel_realtime(self,delay = 0.01):
        """realtime"""
        while True:
            sleep(delay)
            # self.restart()
            print("\033[0;36m%s\033[0m"%self.get_all())

    def zero_one(self,ARM_joint_num):
        """歸零 單一關節"""
        self.data_pub("$H"+self.ARM_joint[ARM_joint_num])

    def zero_all(self):
        """歸零 全部關節(6個)"""
        self.data_pub("$H")

    def goto0(self):
        """移到 [0,0,0,0,0,0]"""
        self.data_pub("$GOTO0")

    def restart(self):
        """重新啟動 串行端口"""
        self.ARM.close()      
        sleep(0.005)
        self.ARM=serial.Serial(self._serial_port,115200,timeout=0.5)

    def set_speed(self,speed):
        self.data_pub("$SPEED"+str(speed))

    def close(self):          
        """關閉 串行端口 """
        self.ARM.close()      
        if setting.realtime == True: 
            self.show_angel_rt.join()
            
class serial_port:
    """
    [search  serial  port]
        :dmesg | grep tty
    """
    system = "windows" # windows,ubuntu
    def __init__(self) :
        pass
    def test(self,serial_port_num):
        """ dmesg | grep tty """ 
        __temp = ""
        try:
            ARM=serial.Serial(serial_port_num,115200,timeout=0.5)
            ARM.write("?\r\n".encode())

            data = ARM.readline().decode()     
            if "<Idle|MPos:" in data: 
                __temp =  data
            else:
                __temp =  "False(find serial port,but not the arm)\ndata => " + data
            ARM.close()
            return __temp
        except Exception as e:
            return "False(serial port not found)\nerror => " + str(e)
    def auto_get(self,count = setting.serial_port_auto_get_count):
        __temp  = "Not found"
        if serial_port.system == "ubuntu":
            for  port in range(0,count):
                if "False" in  serial_port().test("/dev/ttyUSB%s" % port):
                    continue
                else:
                    __temp = "/dev/ttyUSB%s" % port
                    break
            for  port in range(0,count):
                if "False" in  serial_port().test("/dev/ttyACM%s" % port):
                    continue
                else:
                    __temp = "/dev/ttyUSB%s" % port
                    break
        elif serial_port.system == "windows":
            for  port in range(0,count):
                if "False" in  serial_port().test("com%s" % port):
                    continue
                else:
                    __temp = "com%s" % port
                    break
        else: raise ValueError("<serial_port.system> value is 'windows' or 'ubuntu'")
        return __temp      

### arduino gripper ###
# class gripper:
#     """
#     打開arduino , 從檔案->範例->Firmata->StandarFirmata , 來打開草稿碼並且上傳
#     夾爪最小值:0 , 最大值 : 120
#     """
# from pyfirmata2 import Arduino, SERVO
#     signal = 9
#     def  __init__(self,angle):

#         if angle > 120 or angle < 0:
#             raise ValueError("夾爪最小值:0 , 最大值:120")
#         else:
#             board = Arduino(Arduino.AUTODETECT) 
#             board.digital[self.signal].mode = SERVO

#             board.digital[self.signal].write(angle)
#             sleep(0.5)

def __main():


    # a = serial_port().auto_get()
    # print(a)
    # setting.serial_port_auto = False

    # print(serial_port().test(serial_port().auto_get()))
    # setting.realtime = True
    # setting.warning = True
    # setting.set_one_absolute_info = False

    arm = AR3()
    # arm.zero_all()
    # arm.run_way([[0,0,0,0,0,0]])

    # while True:
    #     print(arm.get_all())
    arm.servo(10)
    # print(arm.servo_angle)
    # arm.goto0()
    # sleep(5)
    # arm.set_all_relative(setting.standard_posture)
    # arm.set_all_absolute(setting.standard_posture)
    # sleep(5)
    # arm.set_one_absolute(1,100)
    # arm.run_way([[150,0,0,0,0,0],setting.standard_posture,[0,0,0,0,150,0]])
    # arm.set_all_absolute([301,0,0,0,0,0])
    # sleep(5)
    arm.set_all_absolute(setting.standard_posture)


    # arm.set_all_absolute([0,0,0,0,0,0])


    # arm.zero_all()
    arm.close()

    

    
if __name__ == "__main__":
    __main()
