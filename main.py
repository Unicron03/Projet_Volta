# Programme voiture autonome a completer
import pyb, time
from pyb import delay, Timer

class HBridge:
    """ Control à H-Bridge. Also support PWM to control the speed (between 0 to 100%) """
    PWM_FREQ = 100  # Frequency 100 Hz
    (UNDEFINED,HALT,FORWARD,BACKWARD) = (-1, 0,1,2)

    def __init__( self, input_pins, pwm = None ):
        """:param input_pins: tuple with input1 and input 2 pins
           :param pwm: dic with pin, timer and channel """
        self.speed = 0
        self.state = HBridge.UNDEFINED
        
        # Init HBridge control pins
        self.p_input1 = pyb.Pin( input_pins[0], pyb.Pin.OUT_PP )
        self.p_input2 = pyb.Pin( input_pins[1], pyb.Pin.OUT_PP )

        # Init PWM Control for speed control (without PWM, the L293D's
        #   Enable pin must be place to HIGH level)
        self.has_pwm = (pwm != None)
        if self.has_pwm: 
            self._timer = pyb.Timer( pwm['timer'], freq=self.PWM_FREQ )
            self._channel = self._timer.channel( pwm['channel'], Timer.PWM, pin=pwm['pin'], pulse_width_percent=100 )

        self.halt()

    def set_speed( self, speed ):
        if not(0 <= speed <= 100):
            raise ValueError( 'invalid speed' )
        # Use PWM speed ?
        if self.has_pwm:
            self._channel.pulse_width_percent( speed )
            self.speed = speed
        else:
            # Non PWM
            self.speed = 0 if speed == 0 else 100
            if self.speed == 0 and self.state != HBridge.HALT:
                self.halt() # force motor to stop by manipulating input1 & input2
                
    
    def halt( self ):
        self.p_input1.low()
        self.p_input2.low()
        self.state = HBridge.HALT # Do not invert ...
        self.set_speed( 0 )       #    thoses 2 lines

    def forward(self, speed = 100 ):
        # reconfigure HBridge
        if self.state != HBridge.FORWARD :
            self.halt()
            self.p_input1.low()
            self.p_input2.high()
            self.state = HBridge.FORWARD
        # Set speed
        self.set_speed( speed )
        
    def backward(self, speed = 100 ):
        # reconfigure HBridge
        if self.state != HBridge.BACKWARD:
            self.halt()
            self.p_input1.high()
            self.p_input2.low()
            self.state = HBridge.BACKWARD
        # Set speed 
        self.set_speed( speed )
        

# Pont-H broches de commande Input 1 et Input 2
MOT1_PINS = (pyb.Pin.board.X6, pyb.Pin.board.X5)
# Commande PWM pont-H
MOT1_PWM = {'pin' : pyb.Pin.board.Y9, 'timer' : 2, 'channel' : 3 }   

# Pont-H broches de commande Input 3 et Input 4
MOT2_PINS = (pyb.Pin.board.X7, pyb.Pin.board.X8)
# Commande PWM pont-H
#MOT2_PWM = {'pin' : pyb.Pin.board.X10, 'timer' : 5, 'channel' : 4 }
MOT2_PWM = {'pin' : pyb.Pin.board.Y10, 'timer' : 2, 'channel' : 4 }
# moteur droit h1 moteur gauche h2
h1 = HBridge( MOT1_PINS, MOT1_PWM )
h2 = HBridge( MOT2_PINS, MOT2_PWM )

# bouton sur carte prototype
btn = pyb.Pin( 'Y8', pyb.Pin.IN, pull=pyb.Pin.PULL_UP )
# bouton sur la carte USR
sw = pyb.Switch()
# photoresistance
ldr = pyb.ADC('X19')
# accelerometre
accel = pyb.Accel()
x = accel.x()
SENS = 3
# led sur la carte
led_lum = pyb.LED(1)
led_montee = pyb.LED(2)
led_descente = pyb.LED(3)
xlights = (pyb.LED(3), pyb.LED(4))
# servo direction
sd = pyb.Servo(1)

def dist_obstacle():
    trigger = pyb.Pin(pyb.Pin.board.Y5, mode=pyb.Pin.OUT, pull=None)
    trigger.low()
    echo = pyb.Pin(pyb.Pin.board.Y6, mode=pyb.Pin.IN, pull=None)
    trigger.high()
    time.sleep(0.00001)
    trigger.low()
    while echo.value() == 0:
        pass
    start = time.ticks_us()
    while echo.value() == 1:
        pass
    stop = time.ticks_us()
    return round((stop-start)*34/2000,1)

def lectension():
    lecture = ldr.read()
    tension = (lecture*3.3)/4095
    pyb.delay(100)
    return tension

def forward(speed):
    if speed == 0:
        forward = False
    else:
        forward = True
    return forward
        
#15 speed min     
def allSpeed(speed):
    #print(forward(vitesse()))
    if forward(vitesse()):
        sd.angle(0)
        h1.forward(speed)
        h2.forward(speed)
    else:
        sd.angle(30)
        h1.backward(30)
        h2.backward(30)
        t = 3
        while t:
            mins, secs = divmod(t, 60)
            timer = '{:02d}:{:02d}'.format(mins, secs)
            print(timer, end="\r")
            time.sleep(1)
            t -= 1
        if t == 0:
            sd.angle(30)
            h1.backward(30)
            h2.backward(30)
        
#     if speed == 0:
#         forward = False
#         sd.angle(30)
#     else:
#         forward = True
#         sd.angle(0)
#         
#     if forward == True:
#         h1.forward(speed)
#         h2.forward(speed)
#     else:
#         h1.backward(speed)
#         h2.backward(speed)

def vitesse():
    if accel.x() < 0:
        terrain = lst_terrain[0]
        led_montee.off()
        led_descente.on()
        """led orange = descente"""
        if dist_obstacle() < 10:
            speed = 0
        elif dist_obstacle() < 15:
            speed = 1
        elif dist_obstacle() < 25:
            speed = 2
        elif dist_obstacle() < 40:
            speed = 4
        else:
            speed = 5
            
    elif accel.x() > 4:
        terrain = lst_terrain[1]
        led_descente.off()
        led_montee.on()
        """led verte = montee"""
        if dist_obstacle() < 10:
            speed = 0
        elif dist_obstacle() < 15:
            speed = 15
        elif dist_obstacle() < 25:
            speed = 20
        elif dist_obstacle() < 40:
            speed = 35
        else:
            speed = 50
    else:
        terrain = lst_terrain[2]
        led_descente.off()
        led_montee.off()
        """plat"""
        if dist_obstacle() < 5:
            speed = 0
        elif dist_obstacle() < 15:
            speed = 15
        elif dist_obstacle() < 25:
            speed = 20
        elif dist_obstacle() < 40:
            speed = 35
        else:
            speed = 50
#     else:
#         if dist_obstacle() < 20:
#             speed = 0
#         else:
#             speed = 20
    return speed

marche = True
lst_terrain = ["descente", "montee", "plat"]
sw = pyb.Switch()

while True:
    print(accel.x())
    if lectension() < 1:
        led_lum.on()
    else:
        led_lum.off()
        
    if sw():
        sd.angle(0)
        marche = not marche
        while sw():
            pass
    if marche:
        allSpeed(vitesse())
    else:
        allSpeed(0)
        

    