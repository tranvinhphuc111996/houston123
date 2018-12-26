import RPi.GPIO as GPIO
import MFRC522
import signal
from subprocess import call
from datetime import datetime
from time import sleep
import threading 
from Queue import Queue
import json
import binascii
import requests
import random
import string 
import os.path
from socketIO_client import SocketIO ,BaseNamespace

import sys


get_time = datetime.now() 
name_log = get_time.strftime("%d_%m_%y_%H_%M_%S")
log_stdout = '/home/pi/Documents/log_'+''.join(str(name_log)) + '.log'
import logging
logging.basicConfig(filename=str(log_stdout),level=logging.DEBUG)


url_kltn = 'http://houston123.edu.vn:5000/json/scan_the'
headers = {'Host':'houston123.edu.vn','Accept': '*/*',
      'Content-type': 'application/json'}
url_register_tag = 'http://houston123.edu.vn:5000/json/register_tag'
DeviceID = 1 

GPIO.setwarnings(False) # Ignore warning for now
GPIO.setmode(GPIO.BOARD) # Use physical pin numbering
GPIO.setup(13, GPIO.OUT, initial=GPIO.LOW) # Set pin 8 to be an output pin and set initial value to low (off)
GPIO.setup(15, GPIO.OUT, initial=GPIO.LOW) # Set pin 8 to be an output pin and set initial value to low (off)
# GPIO.setup(12, GPIO.OUT, initial=GPIO.LOW) # Di an thi su dung pin 12 cua chuong
GPIO.setup(7, GPIO.OUT, initial=GPIO.LOW) # Cac trung tam khac su dung chan 7 


DataQueue = Queue()
Check_Register = False




class MFRC522_Thread(threading.Thread):
   def __init__(self):
        threading.Thread.__init__(self)
        self._stopevent = threading.Event()
        self.MIFAREReader = MFRC522.MFRC522()
     
   def run(self):
        try:
            while not self._stopevent.isSet():
                ## Tries to enroll new finger               
                global Check_Register
                if Check_Register == True:
                    sleep(1)
                    pass
                else:
                    (status,TagType) = self.MIFAREReader.MFRC522_Request(self.MIFAREReader.PICC_REQIDL)
                    # If a card is found
                    if status == self.MIFAREReader.MI_OK:
                        logging.debug ("Card detected")
                        # Get the UID of the card
                    (status,uid) = self.MIFAREReader.MFRC522_Anticoll()
                    # Change format UID to hex
                    # If we have the UID, continue
                    if status == self.MIFAREReader.MI_OK:
                        # logging.debug UID
                        threading.Timer(0.0,beep).start()  
                        GPIO.output(13, GPIO.HIGH) # Turn on
                        sleep(0.5) # Sleep for 1 second
                        GPIO.output(13, GPIO.LOW) # Turn off
                        sleep(0.5) # Sleep for 1 second
                    
                        dt = datetime.now()
                    
                        Image_name = 'img'+''.join(random.choice(string.digits) for x in range(15))
                    
                        dtime_string = str(dt.hour)+":"+str(dt.minute)+":"+str(dt.second)+"-"+str(dt.day)+"/"+str(dt.month)+"/"+str(dt.year)
                    
                        call(["fswebcam","-d","/dev/video0", "--no-banner", "/home/pi/Pictures/%s.jpg" % str(Image_name)])
                    
                        hexcode = binascii.hexlify(bytearray(uid)).decode('ascii')
                        logging.debug(hexcode)
                        CardID_Data= json.dumps({'CardID': hexcode,'ImageID': str(Image_name),'EntryTime': str(dtime_string),'dataType':2 ,'uid': hexcode,'imageUrl': str(Image_name),'inout' : 0,'time':  {'h': str(dt.hour),'m': str(dt.minute),'s': str(dt.second),'d':str(dt.day),'mo': str(dt.month),'y': str(dt.year)}})
                        DataQueue.put(CardID_Data)
               
               
        except Exception as e:
            raise e


Scan_Tag = MFRC522_Thread()


class Register_MFRC522_Thread(threading.Thread):
   def __init__(self):
        threading.Thread.__init__(self)
        self._stopevent = threading.Event()
        self.MIFAREReader = MFRC522.MFRC522()
   def run(self):
        try:
            while not self._stopevent.isSet():
                ## Tries to enroll new finger
                (status,TagType) = self.MIFAREReader.MFRC522_Request(self.MIFAREReader.PICC_REQIDL)
                # If a card is found
                if status == self.MIFAREReader.MI_OK:
                    logging.debug ("Register Card  detected")
                    # Get the UID of the card
                (status,uid) = self.MIFAREReader.MFRC522_Anticoll()
                # Change format UID to hex
                # If we have the UID, continue
                if status == self.MIFAREReader.MI_OK:
                    # logging.debug UID
                    GPIO.output(13, GPIO.HIGH) # Turn on
                    sleep(0.5) # Sleep for 1 second
                    GPIO.output(13, GPIO.LOW) # Turn off
                    sleep(0.5) # Sleep for 1 second                
                    hexcode = binascii.hexlify(bytearray(uid)).decode('ascii')
                    logging.debug(hexcode)
                    post_json = json.dumps({"CardID": hexcode})
                    reponse = requests.post(url_register_tag,data=post_json,headers = headers)
                    if reponse.status_code == 200:
                        logging.debug("OK")
                        global Check_Register
                        Check_Register = False
                        break
                        
                   
                sleep(1)
        except Exception as e:
            raise e
        
   def join(self):
        """ Stop the thread. """
        self._stopevent.set()
        self._stopevent.clear()
        threading.Thread.join(self)   

class CheckQueue_Thread(threading.Thread):
   def __init__(self):
        threading.Thread.__init__(self)
    
   def run(self):
        try:
            CardSignal = False
            post_data = {'DeviceID': DeviceID}
            while True:
               
                if(DataQueue.empty() == True):
                # DataQueue.task_done()
                    pass
                else:
                    Data_Parsed = json.loads(DataQueue.get())
                
                    if 'CardID' in Data_Parsed:
                        CardSignal = True
                        post_data.update(Data_Parsed)
                        logging.debug("CardSignal = True")
                    if((CardSignal == True)):
                        logging.debug("send data to sever")
                        post_json = json.dumps(post_data)
            
                        load_data = json.loads(post_json)
                        threading.Timer(0.25,Imagepost,[str(load_data["ImageID"]),post_json]).start()  
                        reponse = requests.post(url_kltn,data=post_json,headers = headers)

                        logging.debug(reponse)
                        if reponse.status_code == 200:
                            GPIO.output(13, GPIO.HIGH) # Turn on
                            sleep(0.5)
                            GPIO.output(13, GPIO.LOW)
                            sleep(0.5)
        
                        if reponse.status_code != 200:
                            GPIO.output(15,GPIO.HIGH)
                            sleep(0.5)
                            GPIO.output(15,GPIO.LOW)
                            sleep(0.5)
                            
                        CardSignal = False
                    
                        
                        
                
        except Exception as e:
            raise e
                  
                  
                  
Check_Queue = CheckQueue_Thread()
                  
                  
def Imagepost(ImageID,post_json):
    url_kltn = 'http://houston123.edu.vn:5000/rev_image'
    # url_houston = 'http://houston123.ddns.net/api/devices/chamcong_test'
    url_houston = 'http://houston123.ddns.net/api/devices/chamcong'

    b = ImageID
    a = '/home/pi/Pictures/' + str(b) +'.jpg'
    if (os.path.isfile(a)) == True:     
        file = {'file': open(a,'rb')}
        file2 = {'file': open(a,'rb')}
        houston_post = json.loads(post_json)
        try:
            houston123_respone = requests.post(url_houston,files=file2,data=houston_post)
        except ConnectionError:
            logging.debug("houston123 fail")

            
        try:
             reponse = requests.post(url_kltn,files=file)
        except ConnectionError:
            logging.debug("kltn fail")
            
       
        logging.debug("upload to sever...")
        logging.debug(reponse.status_code)
        logging.debug(houston123_respone.status_code)
    else: 
        logging.debug("This file not in folder")
        GPIO.output(15,GPIO.HIGH)
        sleep(0.5)
        GPIO.output(15,GPIO.LOW)
        sleep(0.5)
        

def beep():
    # GPIO.output(12, GPIO.HIGH)
    # sleep(1)
    # GPIO.output(12, GPIO.LOW)
    p = GPIO.PWM(7, 4000)
    p.start(25)
    sleep(.07)
    p.stop()



        
class SocketClient_Listener(threading.Thread):
   def __init__(self):
        threading.Thread.__init__(self)
        
        self.socket = SocketIO('http://houston123.edu.vn',5000,wait_for_connection=False)
       
        
   def run(self):
        try:

            _BaseNamespace = self.socket.get_namespace()
            submit_ssid = self.socket.define(BaseNamespace, '/submit_ssid')
            def handle_kick(self):
                logging.debug("DMM")
                global Check_Register
                Check_Register = True
                Thread_Tag_Register = Register_MFRC522_Thread()
                Thread_Tag_Register.start()
                
            def on_connect():
                logging.debug("Connected")
                submit_ssid.emit('submit_sid',{'devID': 1 , 'Descrip': "DIA"})
            def on_reconnect():
                logging.debug('Reconnect')
                submit_ssid.emit('submit_sid',{'devID': 1 , 'Descrip': "DIA"})
            self.socket.on('connect',on_connect())
            _BaseNamespace.on('reconnect',on_reconnect)
            submit_ssid.on('Register_Signal',handle_kick)

            self.socket.wait()
        except Exception as e:
            raise e
SocketClient = SocketClient_Listener()




Scan_Tag.start()
Check_Queue.start()
SocketClient.start()

     
    


    









