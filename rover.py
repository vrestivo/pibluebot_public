#!/usr/bin/python

#this is a simple raspberry pi zero rover
#that communicates with a controller app
#via HC-06 serial bluetooth module

import os, sys, time, RPi.GPIO as G
import threading as thr
import serial


VERSION = "Rover 0.1"

#keeps the main() running
EXIT_SCRIPT = False
OK = False

#serial defice specs
SER_RATE = 115200
SER_PATH = "/dev/ttyAMA0"
ser_dev = None

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

#pwm speed ratio of inner wheels
T_RATIO = 10

#delay how long to run the motors 
DELAY = 0.025

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
  def __init__(self, target=None, direction=None, turn=None,  lock=None, duty_cycle=None):
    self._target = target
    self._direction = direction
    self._turn = turn
    self._lock = lock
    self._duty_cycle = duty_cycle
    super(MoveThread, self).__init__()
  def run(self):
    with self._lock:
      print "Staring "  + self.getName()
      print "There are %d threads running" %thr.activeCount()
      self._target(self._duty_cycle, self._direction, self._turn)
    print "Done with: " + self.getName()



#serial device setup
def serial_setup():
  global SER_PATH
  global ser_dev 
  if os.path.exists(SER_PATH) == True:
    try:
      #timeout=0 turns on non-blocking mode
      ser_dev = serial.Serial(SER_PATH, SER_RATE, timeout=0)
      if ser_dev.isOpen():
        return True
    except serial.SerialException:
      ##
      ser_dev.close()
      sys.exit() 
  else:
    print SER_PATH + " does not exist"
    return False


def terminate():
  global ser_dev
  global EXIT_SCRIPT

  print thr.activeCount()

  while thr.activeCount() > 1 :
    time.sleep(0.1)
    print "Sleeping..."
  

  EXIT_SCRIPT = True


def button_callback(btn):
  print "BUTTON PRESSED: %d" %btn
  print "TERMINATING"
  terminate()

###  GPIO SETUP ###
def gpio_setup():
#set pin numbering mode to Broadcom
  G.setmode(G.BCM)
#TODO delete
### Used for testing purposes only ###
#set BUTTON pin to input
#			set internal pull up resistor
#		      	|
#			v
#  G.setup(BUTTON, G.IN, pull_up_down=G.PUD_UP)
#  G.setup(BUTTON1, G.IN, pull_up_down=G.PUD_UP)

  


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
  #PWM_A = G.PWM(PIN_PWM_A, FREQ)
  #PWM_B = G.PWM(PIN_PWM_B, FREQ)
  #PWM_A.start(50)
  #PWM_B.start(50)


#TODO delete
def toggleGPIO(state, pin):
  G.output(pin, True)
  print "PIN %d" %pin + "LED ON"
  time.sleep(0.005)
  G.output(pin, False)
  print "PIN %d" %pin +"LED OFF"

#function for moving forward
def move(duty_cycle=None, direction=None, turn=None):

  #move forward
  if turn == None and direction == True:
    print "fwd"
    G.output(PIN_FWD_A, True)
    G.output(PIN_FWD_B, True)
    G.output(PIN_PWM_A, True)
    G.output(PIN_PWM_B, True)
    
    time.sleep(DELAY)
    
    G.output(PIN_PWM_A, False)
    G.output(PIN_PWM_B, False)
    G.output(PIN_FWD_A, False)
    G.output(PIN_FWD_B, False)

  #move in reverse
  elif turn == None and direction == False:
    print "rev"
    G.output(PIN_REV_A, True)
    G.output(PIN_REV_B, True)
    G.output(PIN_PWM_A, True)
    G.output(PIN_PWM_B, True)

    time.sleep(DELAY)

    G.output(PIN_PWM_A, False)
    G.output(PIN_PWM_B, False)
    G.output(PIN_REV_A, False)
    G.output(PIN_REV_B, False)

  #turn right (forward right)
  elif turn == True and direction == True:
    print "right"
    G.output(PIN_FWD_B, True)
    G.output(PIN_PWM_B, True)
     
    time.sleep(DELAY)

    G.output(PIN_PWM_B, False)
    G.output(PIN_FWD_B, False)

  #turn left (forward left)
  elif turn == False and direction == True:
    print "left"
    G.output(PIN_FWD_A, True)
    G.output(PIN_PWM_A, True)
     
    time.sleep(DELAY)
    
    G.output(PIN_PWM_A, False)
    G.output(PIN_FWD_A, False)

  else:
    pass


def main():
  global EXIT_SCRIPT
  global OK
  global ser_dev 
 
  if serial_setup() == True:
    gpio_setup()
  else: sys.exit()


  
  while not EXIT_SCRIPT:
    #TODO read serial and perform action
    try:
      c = ser_dev.read()

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
      else:
        #reserved for expaded functionality
        pass
 
    except serial.SerialException:
      ser_dev.close() 
      EXIT_SCRIPT = True  
 
  ser_dev.close(); 

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
    print "Cleaning up..."
    ser_dev.close()
    G.cleanup()
    print "Done!"

