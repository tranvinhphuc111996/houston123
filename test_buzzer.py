import RPi.GPIO as GPIO
from time import sleep


GPIO.setwarnings(False) # Ignore warning for now
GPIO.setmode(GPIO.BOARD) # Use physical pin numbering
GPIO.setup(7, GPIO.OUT, initial=GPIO.LOW) # Cac trung tam khac su dung chan 7 

def beep():
    # GPIO.output(12, GPIO.HIGH)
    # sleep(1)
    # GPIO.output(12, GPIO.LOW)
    p = GPIO.PWM(7, 4000)
    p.start(25)
    sleep(.07)
    p.stop()

while 1:
    beep()
    sleep(1)