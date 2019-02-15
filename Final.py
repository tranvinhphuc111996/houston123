import RPi.GPIO as GPIO
import MFRC522
import signal
from subprocess import call
from datetime import datetime
from time import sleep
import threading 
import multiprocessing 
from Queue import Queue
import json
import binascii
import requests
import random
import string 
import os.path
from socketIO_client import SocketIO ,BaseNamespace
from pyfingerprint import PyFingerprint
import os
import sys
import sqlite3


url_kltn = 'http://houston123.edu.vn:5000/json/scan_the'
headers = {'Host':'houston123.edu.vn','Accept': '*/*',
      'Content-type': 'application/json'}
url_register_tag = 'http://houston123.edu.vn:5000/json/register_tag'
DeviceID = 1 

GPIO.setwarnings(False) # Ignore warning for now
GPIO.setmode(GPIO.BOARD) # Use physical pin numbering
GPIO.setup(13, GPIO.OUT, initial=GPIO.LOW) # Set pin 8 to be an output pin and set initial value to low (off)
GPIO.setup(15, GPIO.OUT, initial=GPIO.LOW) # Set pin 8 to be an output pin and set initial value to low (off)
GPIO.setup(7, GPIO.OUT, initial=GPIO.LOW)


DataQueue = Queue()
Finger_Queue = multiprocessing.Queue()

 
Finger_Scanning = True

global_pid = 2222
DATABASE_FILE = 'backupdatabase.db'
def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def connectdb():
    conn = sqlite3.connect(DATABASE_FILE, isolation_level = None)
    return conn

def querydb(conn, query, v = tuple()):
    c = conn.cursor()
    c.row_factory = dict_factory
    c.execute(query, v)
    return c.fetchall()


try:
    fingerserial = PyFingerprint('/dev/ttyUSB0', 57600, 0xFFFFFFFF, 0x00000000)

    if not fingerserial.verifyPassword():
        raise ValueError('The given fingerprint sensor password is wrong!')

except Exception as e:
    print('The fingerprint sensor could not be initialized!')
    print('Exception message: ' + str(e))    


class MFRC522_Thread(threading.Thread):
   def __init__(self):
        threading.Thread.__init__(self)
        self._stopevent = threading.Event()
        self.Check_Register = threading.Event()
        self.MIFAREReader = MFRC522.MFRC522()
     
   def run(self):
        

        try:
            while not self._stopevent.isSet():
                ## Tries to enroll new finger   
                
                if self.Check_Register.isSet() == True:
                    print(self.Check_Register.isSet())
                    pass
                else:
                    (status,TagType) = self.MIFAREReader.MFRC522_Request(self.MIFAREReader.PICC_REQIDL)
                    # If a card is found
                    if status == self.MIFAREReader.MI_OK:
                        print ("Card detected")
                        # Get the UID of the card
                    (status,uid) = self.MIFAREReader.MFRC522_Anticoll()
                    # Change format UID to hex
                    # If we have the UID, continue
                    if status == self.MIFAREReader.MI_OK:
                        # Print UID
                        beep()
                        GPIO.output(13, GPIO.HIGH) # Turn on
                        sleep(0.5) # Sleep for 1 second
                        GPIO.output(13, GPIO.LOW) # Turn off
                        
                    
                        dt = datetime.now()
                    
                        Image_name = 'img'+''.join(random.choice(string.digits) for x in range(15))
                    
                        dtime_string = str(dt.hour)+":"+str(dt.minute)+":"+str(dt.second)+"-"+str(dt.day)+"/"+str(dt.month)+"/"+str(dt.year)
                    
                        call(["fswebcam","-d","/dev/video0", "--no-banner", "./capture/%s.jpg" % str(Image_name)])
                    
                        hexcode = binascii.hexlify(bytearray(uid)).decode('ascii')
                        print(hexcode)
                        CardID_Data= json.dumps({'CardID': hexcode,'ImageID': str(Image_name),'EntryTime': str(dtime_string),'imageUrl': str(Image_name)})
                        DataQueue.put(CardID_Data)
                sleep(0.5)
               
        except Exception as e:
            raise e
        
   def join(self):
        """ Stop the thread. """
        self.Check_Register.clear()
        threading.Thread.join(self)   


Scan_Tag = MFRC522_Thread()


class Register_MFRC522_Thread(threading.Thread):
   def __init__(self):
        threading.Thread.__init__(self)
        self._stopevent = threading.Event()
        self.MIFAREReader = MFRC522.MFRC522()
   def run(self):
        try:
            global Finger_Enroll
            global Finger_Enroll_Event
            global Finger_Create_Enroll_Event
            global fingerserial
            global Scan_Tag
            global global_pid

            while not self._stopevent.isSet():
                print('Finger_Create_Enroll_Event',Finger_Create_Enroll_Event.is_set())
                print('Finger_Enroll_Event',Finger_Enroll_Event.is_set())
                
                ## Tries to enroll new finger
                (status,TagType) = self.MIFAREReader.MFRC522_Request(self.MIFAREReader.PICC_REQIDL)
                # If a card is found
                if status == self.MIFAREReader.MI_OK:
                    print ("Register Card  detected")
                    # Get the UID of the card
                (status,uid) = self.MIFAREReader.MFRC522_Anticoll()
                # Change format UID to hex
                # If we have the UID, continue
                if status == self.MIFAREReader.MI_OK:
                    # Print UID
                    GPIO.output(13, GPIO.HIGH) # Turn on
                    sleep(0.5) # Sleep for 1 second
                    GPIO.output(13, GPIO.LOW) # Turn off
                             
                    hexcode = binascii.hexlify(bytearray(uid)).decode('ascii')
                    print(hexcode)
                    post_json = json.dumps({"CardID": hexcode})
                    reponse = requests.post(url_register_tag,data=post_json,headers = headers)
                    if reponse.status_code == 200:
                        print("OK")

                        
                        if Finger_Create_Enroll_Event.is_set():
                            if global_pid == 0:
                                # os.kill(global_pid, signal.SIGKILL )
                                print('Finger_Create_Enroll_Event  ' ,global_pid)
                                Finger_Enroll_Event.set()
                                Finger_Enroll = multiprocessing.Process(target=Finger_Scan_Enroll, args=(fingerserial,Finger_Enroll_Event,Finger_Create_Enroll_Event,))
                                Finger_Enroll.start()
                            else:
                                print('Finger_Create_Enroll_Event' , Finger_Create_Enroll_Event.is_set())
                                Finger_Enroll = multiprocessing.Process(target=Finger_Scan_Enroll, args=(fingerserial,Finger_Enroll_Event,Finger_Create_Enroll_Event,))
                                print('Finger_Enroll = multiprocessing.Process')
                                Finger_Enroll.start()
                                Finger_Enroll_Event.set()
                                print('Finger_Enroll = multiprocessing.Process')
                            Scan_Tag.join()
                            Scan_Tag.Check_Register.clear()
                            Finger_Enroll_Event.set()

                            print( 'Finger_Enroll_Event.set()')



                        else:
                            Scan_Tag.Check_Register.clear()
                            Finger_Enroll.start()
                            print( 'Finger_Enroll.start()')
                            Finger_Enroll_Event.set()
                            print( 'Finger_Enroll_Event.set()')
                            Finger_Create_Enroll_Event.set()
                            print( 'Finger_Create_Enroll_Event.set()')
                    
                    break
                   
                sleep(1)
        except Exception as e:
            raise e
        
   def join(self):
        """ Stop the thread. """
        self._stopevent.set()
        self._stopevent.clear()
        threading.Thread.join(self)   
def Finger_Scan_Func(f,Queue,Finger_Scan_Event,Finger_lock):
    
    global Finger_Register
    global Finger_Scanning  
    global Finger_Enroll
    global Finger_Enroll_Event
    while Finger_Scanning == True:
        
        try:

            if(Finger_Scan_Event.is_set() == True):
                Finger_lock.acquire()
                Finger_lock.wait()
                Finger_lock.release()
                pass
            print('Waiting for finger...')
            ### Wait that finger is read
            while not Finger_Scan_Event.is_set():
                
                if f.readImage() == False:
                    pass
                else:    
                    ## Converts read image to characteristics and stores it in charbuffer 1
                    f.convertImage(0x01)
                    result = f.searchTemplate()
                    positionNumber = result[0]
                    accuracyScore = result[1]

                    if ( positionNumber == -1 ):
                        print('No match found!')
                        GPIO.output(15, GPIO.HIGH) # Turn on
                        sleep(0.5) # Sleep for 1 second
                        GPIO.output(15, GPIO.LOW) # Turn off
                        pass
                    else:
                        print('Found template at position #' + str(positionNumber))
                        print('The accuracy score is: ' + str(accuracyScore))
                       
                        fingerprint = str(f.downloadCharacteristics(0x01))
                        dt = datetime.now()
                        Image_name = 'img'+''.join(random.choice(string.digits) for x in range(15))
                        dtime_string = str(dt.hour)+":"+str(dt.minute)+":"+str(dt.second)+"-"+str(dt.day)+"/"+str(dt.month)+"/"+str(dt.year)
                        call(["fswebcam","-d","/dev/video0", "--no-banner", "./capture/%s.jpg" % str(Image_name)])
                        Fingerprint_data= json.dumps({'FingerID': fingerprint,'PositionNumber': positionNumber,'ImageID': str(Image_name),'EntryTime': str(dtime_string), 'imageUrl': str(Image_name)})
                        Finger_Queue.put(Fingerprint_data)
        except Exception as e:
            print('Operation failed!')
            print('Exception message: ' + str(e))
            pass
        sleep(1)
Finger_Scan_Event = multiprocessing.Event()
Finger_lock = multiprocessing.Condition()
Finger_Scan = multiprocessing.Process(target=Finger_Scan_Func, args=(fingerserial,DataQueue,Finger_Scan_Event,Finger_lock,))

def Finger_Scan_Enroll(f,Finger_Enroll_Event,Finger_Create_Enroll_Event):
    global Finger_Scan_Event
    global Finger_lock
    global Scan_Tag
    global global_pid
    ## Tries to enroll new finger
    headers = {'Host':'houston123.edu.vn','Accept': '*/*',
      'Content-type': 'application/json'}
    url_register_tag = 'http://houston123.edu.vn:5000/json/register_finger'
    print('Finger_Scan_Enroll')
    print('Finger_Enroll_Event.is_set()',Finger_Enroll_Event.is_set())
    while Finger_Enroll_Event.is_set():
        global_pid = os.getpid()
        print(global_pid)
        print( 'Finger_Enroll_Event.set()')
        try:
            print('Waiting for Register finger...')
            ## Wait that finger is read
            while ( f.readImage() == False ):
                pass
            ## Converts read image to characteristics and stores it in charbuffer 1
            f.convertImage(0x01)
            ## Checks if finger is already enrolled
            result = f.searchTemplate()
            positionNumber = result[0]

            if ( positionNumber >= 0 ):
                print('Template already exists at position #' + str(positionNumber))
                GPIO.output(15,GPIO.HIGH)
                sleep(0.5)
                GPIO.output(15,GPIO.LOW)
                global Finger_Scan
                Scan_Tag.Check_Register.clear()
                Scan_Tag.join()
                Finger_Scan_Event.clear()
                sleep(1)
                Finger_Enroll_Event.clear()
                Finger_lock.acquire()
                Finger_lock.notify()
                Finger_lock.release()
                os.kill(os.getpid(), signal.SIGKILL )
                pass
            else:
                print('Remove Register finger...')
                sleep(2)
                print('Waiting for same Register finger again...')
                ## Wait that finger is read again
                while ( f.readImage() == False ):
                    pass
                ## Converts read image to characteristics and stores it in charbuffer 2
                f.convertImage(0x02)
                ## Compares the charbuffers
                if ( f.compareCharacteristics() == 0 ):
                    raise Exception('Fingers do not match')
                    GPIO.output(15,GPIO.HIGH)
                    sleep(0.5)
                    GPIO.output(15,GPIO.LOW)
                    Scan_Tag.Check_Register.clear()
                    Scan_Tag.join()
                    Scan_Tag.Check_Register.clear()
                    
                    Finger_Scan_Event.clear()
                    sleep(1)
                    Finger_Enroll_Event.clear()
                    Finger_lock.acquire()
                    Finger_lock.notify()
                    Finger_lock.release()
                    os.kill(os.getpid(), signal.SIGKILL )
                    pass
                ## Creates a template
                f.createTemplate()
                ## Saves template at new position number
                positionNumber = f.storeTemplate()
                print('Finger enrolled successfully!')
                print('New template position #' + str(positionNumber))
                post_json = json.dumps({"FingerID": positionNumber})
                reponse = requests.post(url_register_tag,data=post_json,headers = headers)
                Scan_Tag.Check_Register.clear()
                Scan_Tag.join()
              
                Finger_Scan_Event.clear()
                sleep(1)
                Finger_Enroll_Event.clear()
                Finger_lock.acquire()
                Finger_lock.notify()
                Finger_lock.release()
                os.kill(os.getpid(), signal.SIGKILL )
        except Exception as e:
            print('Operation failed!')
            print('Exception message: ' + str(e))
            GPIO.output(15,GPIO.HIGH)
            sleep(0.5)
            GPIO.output(15,GPIO.LOW)
            Scan_Tag.Check_Register.clear()
            Scan_Tag.join()
            Finger_Scan_Event.clear()
            sleep(1)
            Finger_Enroll_Event.clear()
            Finger_lock.acquire()
            Finger_lock.notify()
            Finger_lock.release()
            os.kill(os.getpid(), signal.SIGKILL )
            pass

Finger_Enroll_Event = multiprocessing.Event()
Finger_Create_Enroll_Event = multiprocessing.Event()
Finger_Enroll = multiprocessing.Process(target=Finger_Scan_Enroll, args=(fingerserial,Finger_Enroll_Event,Finger_Create_Enroll_Event,))
def connected_to_internet(url, timeout):
    try:
        _ = requests.get(url, timeout=timeout)
        return True
    except requests.ConnectionError:
        print("No internet connection available.")
    return False
class CheckQueue_Thread(threading.Thread):
   def __init__(self):
        threading.Thread.__init__(self)
    
   def run(self):
        try:

            while True:
               
                if(DataQueue.empty() == True) and (Finger_Queue.empty() == True) :
                        pass     
                else:
                    # check queue which have data
                    if(DataQueue.empty() != True):
                        Data_Parsed1 = json.loads(DataQueue.get())
                        if 'CardID' in Data_Parsed1:
                            
                            RFID_Postdata = {'DeviceID': DeviceID}
                            RFID_Postdata.update(Data_Parsed1)
                            print("RFID Post")
                            print("send data to sever")
                            RFID_Postdata = json.dumps(RFID_Postdata)
                            load_data = json.loads(RFID_Postdata)   
                            try:           
                                
                                if(connected_to_internet(url_kltn,2)):
                                    reponse = requests.post(url_kltn,data=RFID_Postdata,headers = headers)
                                    rep = json.loads(reponse.text)
                                    
                                    if rep["status"] == 1:
                                        threading.Timer(0.75,Imagepost,[str(load_data["ImageID"]),RFID_Postdata]).start()
                                    if reponse.status_code == 200:
                                        GPIO.output(13, GPIO.HIGH) # Turn on
                                        sleep(0.5)
                                        GPIO.output(13, GPIO.LOW)   
                                    if reponse.status_code != 200:
                                        GPIO.output(15,GPIO.HIGH)
                                        sleep(0.5)
                                        GPIO.output(15,GPIO.LOW)
                                else:
                                    conn = connectdb()
                                    querydb(conn, r"INSERT INTO Work(DeviceID,CardID,FingerID,ImageID,EntryTime) VALUES (?,?,?,?,?)", (DeviceID,CardID,PositionNumber,ImageID,EntryTime, ))
                            except requests.ConnectionError:
                                #save log
                                conn = connectdb()
                                querydb(conn, r"INSERT INTO Work(DeviceID,CardID,FingerID,ImageID,EntryTime) VALUES (?,?,?,?,?)", (DeviceID,CardID,PositionNumber,ImageID,EntryTime, ))
                                print("ConnectionError")

                    if(Finger_Queue.empty() != True):
                        Data_Parsed2 = json.loads(Finger_Queue.get())
                        if 'FingerID' in Data_Parsed2:
                            print("Finger Post")
                            Finger_Postdata = {'DeviceID': DeviceID}
                            Finger_Postdata.update(Data_Parsed2)
                            print("send data to sever")
                            Finger_Postdata = json.dumps(Finger_Postdata)
                            load_data = json.loads(Finger_Postdata)
                            
                            print(load_data)
                            try: 
                                if(connected_to_internet(url_kltn,2)):
                                    reponse = requests.post(url_kltn,data=Finger_Postdata,headers = headers)
                                    rep = json.loads(reponse.text)
                                    print(rep["status"])
                                    if rep["status"] == 1:
                                        threading.Timer(0.75,Imagepost,[str(load_data["ImageID"]),Finger_Postdata]).start()
                                    if reponse.status_code == 200:
                                        GPIO.output(13, GPIO.HIGH) # Turn on
                                        sleep(0.5)
                                        GPIO.output(13, GPIO.LOW)
                                    if reponse.status_code != 200:
                                        GPIO.output(15,GPIO.HIGH)
                                        sleep(0.5)
                                        GPIO.output(15,GPIO.LOW)
                                else:
                                    conn = connectdb()
                                    querydb(conn, r"INSERT INTO Work(DeviceID,CardID,FingerID,ImageID,EntryTime) VALUES (?,?,?,?,?)", (DeviceID,CardID,PositionNumber,ImageID,EntryTime, )) 
                            except requests.ConnectionError:
                                   conn = connectdb()
                                   querydb(conn, r"INSERT INTO Work(DeviceID,CardID,FingerID,ImageID,EntryTime) VALUES (?,?,?,?,?)", (DeviceID,CardID,PositionNumber,ImageID,EntryTime, ))
        except Exception as e:
            raise e
                  
                  
                  
Check_Queue = CheckQueue_Thread()
                  
                  
def Imagepost(ImageID,post_json):
    url_kltn = 'http://houston123.edu.vn:5000/rev_image'
    headers = {'Host':'houston123.edu.vn','Accept': '*/*',
    'Content-type': 'image/png'}
    b = ImageID
    a = './capture/' + str(b) +'.jpg'
    
    if (os.path.isfile(a)) == True:     
        file = {'file': open(a,'rb')}
        reponse1 = requests.post(url_kltn,files=file)
        print("upload to sever...")
        print(reponse1.status_code)  
    else: 
        print("This file not in folder")
        GPIO.output(15,GPIO.HIGH)
        sleep(0.5)
        GPIO.output(15,GPIO.LOW)
        sleep(0.5)
        

def beep():
    p = GPIO.PWM(7, 4650)
    p.start(10)
    sleep(.07)
    p.stop()
class SocketClient_Listener(threading.Thread):
   def __init__(self):
        threading.Thread.__init__(self)
        self.socket = SocketIO('http://houston123.edu.vn',5000,wait_for_connection=False)
        
   def run(self):
      

        try:
            submit_ssid = self.socket.define(BaseNamespace, '/submit_ssid')
            def handle_kick(self):
               
               
                global Finger_Scan
                global Finger_Enroll
                global fingerserial
                global Finger_Scan_Event
                global Scan_Tag
                global global_pid
                global Finger_Create_Enroll_Event
                Scan_Tag.Check_Register.set()
                print("Register Signal")
                Thread_Tag_Register = Register_MFRC522_Thread()
                Thread_Tag_Register.start()
                Finger_Scan_Event.set()
            def on_connect():
                print("Connected")
                submit_ssid.emit('submit_sid',{'devID': 1 , 'Descrip': "Di An"})
            self.socket.on('connect',on_connect())
            submit_ssid.on('Register_Signal',handle_kick)
            self.socket.wait()
        except Exception as e:
            raise e
SocketClient = SocketClient_Listener()




Scan_Tag.start()
Check_Queue.start()
Finger_Scan.start()
SocketClient.start()



    
