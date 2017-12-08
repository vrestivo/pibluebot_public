#!/usr/bin/python

# This is an updated version of Raspberry Pi Zero rover.
# This version is tailored towards Raspberry Pi Zero W.
# It no longer used HC-06 serial bluetooth module,
# since Pi Zero W has an internal bluetooth adapter.
# Most of the changes will reflect the used of internal
# Bluetooth interface.

import os, sys, time, RPi.GPIO as G
import threading as thr
import serial
import re
import time

VERSION = "Rover 0.2"

#keeps the main() running
EXIT_SCRIPT = False
OK = False

#serial defice specs

#by default Raspbian hciattach is started at this rate
SER_RATE = 3000000

#rfcomm socket to listen on
SER_PATH = "/dev/rfcomm0"
ser_dev = None
SER_READY = False

#declaring 'constants'
#TODO delete
BUTTON = 21
LED_OK = 20 

#pins controlling right motors
PIN_FWD_A = 17
PIN_REV_A = 27
PIN_PWM_A = 22

#pins controlling left motors
PIN_FWD_B = 18
PIN_REV_B = 23
PIN_PWM_B = 24 

#gpio pwm pin object
PWM_A = None
PWM_B = None

#pwm frequency 
FREQ = 10000

#delay how long to run the motors 
DELAY = 0.00755555

#define right and left diections
R = True
L = False

#define forward and reverse
FWD = True
REV = False

#a lock for movement actions
#prevents unwanted unsynchronized gpio access
LOCK_MOVE = thr.Lock()


#extend threading's Thread class to run GPIO movement tasks 
class MoveThread(thr.Thread):
  def __init__(self, target=None, x=None, y=None, duty_cycle=None, lock=None):
    self._target = target
    self._x = x
    self._y = y
    self._lock = lock
    self._duty_cycle = duty_cycle
    super(MoveThread, self).__init__()
  def run(self):
    with self._lock:
      print "Staring "  + self.getName()
      print "There are %d threads running" %thr.activeCount()
      self._target(self._x, self._y, self._duty_cycle)
    print "Done with: " + self.getName()



#serial device setup
def serial_setup():
  global SER_PATH
  global ser_dev
  global SER_READY
 
  if os.path.exists(SER_PATH) == True:
    try:
      #timeout=0 turns on non-blocking mode
      ser_dev = serial.Serial(SER_PATH, SER_RATE, timeout=0)
      if ser_dev.isOpen():
        SER_READY = True
    except serial.SerialException:
      if ser_dev != None:
        ser_dev.close()
      SER_READY = False
      ser_dev = None
      #pass
      #sys.exc_clear()
      #sys.exit() 
  else:
    print SER_PATH + " does not exist"
    SER_READY = False
    return False


def terminate():
  global EXIT_SCRIPT
  global SER_READY
  global ser_dev

  print thr.activeCount()

  while thr.activeCount() > 1 :
    time.sleep(0.1)
    print "Sleeping..."
  
  if ser_dev != None:
    ser_dev.close()
    ser_dev = None

  SER_READY = False
  EXIT_SCRIPT = True


def button_callback(btn):
  print "BUTTON PRESSED: %d" %btn
  print "TERMINATING"
  terminate()

###  GPIO SETUP ###
def gpio_setup():

  #set pin numbering mode to Broadcom
  G.setmode(G.BCM)

  global PWM_A
  global PWM_B 


#set pin modes to output
  G.setup(PIN_FWD_A, G.OUT)
  G.setup(PIN_FWD_B, G.OUT)
  G.setup(PIN_REV_A, G.OUT)
  G.setup(PIN_REV_B, G.OUT)
  G.setup(PIN_PWM_A, G.OUT)
  G.setup(PIN_PWM_B, G.OUT)

#set ok led
  G.setup(LED_OK, G.OUT)

#set interrupt BUTTON
  G.setup(BUTTON, G.IN, pull_up_down=G.PUD_UP)
  G.add_event_detect(BUTTON, G.FALLING, callback=button_callback)

#setup pwm
  PWM_A = G.PWM(PIN_PWM_A, FREQ)
  PWM_B = G.PWM(PIN_PWM_B, FREQ)
  PWM_A.start(0)
  PWM_B.start(0)

def move(x=None, y=None, duty_cycle=None):
  global PWM_A
  global PWM_B

  PIN_A = None
  PIN_B = None

  left_dc = 0;
  right_dc = 0;

  #forward 
  if y > 0:
    PIN_A = PIN_FWD_A
    PIN_B = PIN_FWD_B
  #reverse
  else:
    PIN_A = PIN_REV_A
    PIN_B = PIN_REV_B

  #TODO left/right ratio
  if x < 0:
    left_dc = int((x+100)*(1.0)/100*(duty_cycle))
    right_dc = duty_cycle
  else:
    right_dc = int((100-x)*(1.0)/100*(duty_cycle))
    left_dc = duty_cycle	
 
  print "PIN_A %d, PIN_B %d" %(PIN_A, PIN_B)
  print "DC: %d, l_dc, %d r_dc %d" %(duty_cycle, left_dc, right_dc)
  G.output(PIN_A, True)
  G.output(PIN_B, True)
    
  PWM_A.ChangeDutyCycle(left_dc)
  PWM_B.ChangeDutyCycle(right_dc)
    
  time.sleep(DELAY)
    
  PWM_A.ChangeDutyCycle(0)
  PWM_B.ChangeDutyCycle(0)

  G.output(PIN_A, False)
  G.output(PIN_B, False)


def blink_ok_led():
  G.output(LED_OK, False)
  G.output(LED_OK, True)
  time.sleep(.250)
  G.output(LED_OK, False)
  time.sleep(.250)


def main():
  global EXIT_SCRIPT
  global ser_dev 
  global OK
  global SER_READY
 
# change due to new rfcomm behavior 
#  if serial_setup() == True:
#    gpio_setup()
#  else: sys.exit()

#NOTE:  /dev/rfcomm0 will not be open until another
#	bluetooth device is connected to our pi zero W.
# 	Therefore, we have to keep checking until the
#	controller device connects to us.


# setup GPIO
  gpio_setup()

  
  while not EXIT_SCRIPT:

    if ser_dev == None:
      while SER_READY == False and EXIT_SCRIPT == False:
	blink_ok_led()
        serial_setup()

    while SER_READY == True:
      OK = True
      try:
        c = ser_dev.readline()
      
        #FIXME add status for waiting for connection 

        # set ok to true opon successful data read
        OK = True

        if OK:
          G.output(LED_OK, OK)
        else:
          G.output(LED_OK, OK)

        if c == "W":
          print "read in: %s" %c
          fwdThread = MoveThread(target=move, direction=FWD, duty_cycle=100, lock=LOCK_MOVE)
          fwdThread.start()
        elif c == "S":
          print "read in: %s" %c
          fwdThread = MoveThread(target=move, direction=REV, duty_cycle=100, lock=LOCK_MOVE)
          fwdThread.start()
        elif c == "D": 
          print "read in: %s" %c
          fwdThread = MoveThread(target=move, direction=FWD, turn=R,  duty_cycle=100, lock=LOCK_MOVE)
          fwdThread.start()
        elif c == "A":
          print "read in: %s" %c
          fwdThread = MoveThread(target=move, direction=FWD, turn=L, duty_cycle=100, lock=LOCK_MOVE)
          fwdThread.start()
        elif c == "C": 
          print "read in: %s" %c
          fwdThread = MoveThread(target=move, direction=REV, turn=R,  duty_cycle=100, lock=LOCK_MOVE)
          fwdThread.start()
        elif c == "Z":
          print "read in: %s" %c
          fwdThread = MoveThread(target=move, direction=REV, turn=L, duty_cycle=100, lock=LOCK_MOVE)
          fwdThread.start()


        else:
          #reserved for expaded functionality
	  regex = r"((XYR)([\:][\-]?[\d]+)*)"
	  match = re.match(regex, c)
	  if match != None:
	    if match.group(0):
              print "matched: %s" % match.group(0)
	      process_data_string(match.group(0))	
          pass
 

      except serial.SerialException:
        if ser_dev != None:
          ser_dev.close()
	  ser_dev = None
	  SER_READY = False
          #pass
          #sys.exc_clear()

        #EXIT_SCRIPT = True  
  if ser_dev != None: 
    ser_dev.close(); 

def process_data_string(data_string):
  if data_string != None and type(data_string) == type(""):
    l = data_string.split(":")
    if len(l)==4:
      print l
      x = int(l[1])
      y = int(l[2])
      r = int(l[3])

    #TODO
      fwdThread = MoveThread(target=move, x=x, y=y, duty_cycle=r, lock=LOCK_MOVE)
      fwdThread.start()

   

#run the program
if __name__ == "__main__":


  try:
    main()
    if thr.activeCount() > 1:
      time.sleep(.1)

    print "Cleaning up..."
    G.cleanup()
    print "Cleanup complete"
    print "Powering Off!"
    os.system("sudo shutdown -h now")
    
    
  except (KeyboardInterrupt, SystemExit):
    #EXIT_SCRIPT = True
    print "Cleaning up..."
    if ser_dev != None:
      ser_dev.close()
    G.cleanup()
    print "Done!"


