#pliki z keycodeami do klawiatury /usr/include/X11

import os
import sys
from serial import Serial, SerialException
from evdev import InputDevice, categorize, ecodes


#presetet strings to be sent by serial
mute = "m".encode("UTF-8")
unmute = "u".encode("UTF-8")
buzzer = "b".encode("UTF-8")
class Parser:
    def __init__(self):
        # initial state
        self.muted = True
        self.unmuted = False
        self.headphones = False
        self.windows_max = False
        self.backspace_pressed = False

        self.actions_dict = {}

        def key_backspace(key):
            if key.keystate == key.key_hold or key.keystate == key.key_down:
                self.backspace_pressed = True
            else:
                self.backspace_pressed = False
        self.actions_dict['KEY_BACKSPACE'] = lambda key : key_backspace(key)
        self.actions_dict['KEY_KP6'] = lambda key : os.system('xdotool key XF86AudioRaiseVolume')
        self.actions_dict['KEY_KP4'] = lambda key : os.system('xdotool key XF86AudioLowerVolume')
        self.actions_dict['KEY_KP5'] = lambda key : os.system('xdotool key XF86AudioMute')
        self.actions_dict['KEY_KP1'] = lambda key : (
            arduino.write(buzzer) if self.backspace_pressed 
            else os.system('xdotool key XF86AudioPrev')
            )
        self.actions_dict['KEY_KP2'] = lambda key : os.system('xdotool key XF86AudioPlay')
        self.actions_dict['KEY_KP3'] = lambda key : os.system('xdotool key XF86AudioNext')
        def key_kp0(key):
              os.system('xdotool key alt alt+shift+Home')
              if self.muted:
                  arduino.write(unmute)
                  self.unmuted = True
                  self.muted = False
              elif unmuted:
                  arduino.write(mute)
                  self.unmuted = False
                  self.muted = True
        self.actions_dict['KEY_KP0'] = lambda key : key_kp0(key)
        def kp_dot(key):
            print(headphones)
            if self.headphones == 1:
                os.system('/home/karolh/Desktop/skrypty/makra/movesinks.sh ' + sink1)
                self.headphones = 0
            else:
                os.system('/home/karolh/Desktop/skrypty/makra/movesinks.sh ' + sink2)
                self.headphones = 1
        self.actions_dict['KEY_KPDOT'] = lambda key : kp_dot(key)
        def kp_minus(key):
              if self.backspace_pressed:
                  os.system("xdotool key Super_L+Right")
              else:
                  pass            
        self.actions_dict['KEY_KPMINUS'] = lambda key : kp_minus(key)
        self.actions_dict['KEY_KPPLUS'] = lambda key : os.system("xdotool key Super_L+3")
        def kp7(key):
              if self.backspace_pressed:
                  os.system("xdotool key Super_L+Shift+Left")
              else:
                  os.system("xdotool key ctrl+Super_L+F4")
        self.actions_dict['KEY_KP7'] = lambda key : kp7(key) 
        def kp8(key):
              if self.backspace_pressed:
                  os.system("xdotool key Super_L+Shift+Down")
              else:
                  os.system("xdotool key ctrl+Super_L+F5")
        self.actions_dict['KEY_KP8'] = lambda key : kp8(key)
        def kp9(key):
              if self.backspace_pressed:
                  os.system("xdotool key Super_L+Left")
              else:
                  os.system("xdotool key ctrl+Super_L+F6")
        self.actions_dict['KEY_KP9'] = lambda key : kp9(key)
        def key_tab(key):
              if self.backspace_pressed:
                  os.system("xdotool key Super_L+Shift+Up")
              else:
                  os.system("xdotool key ctrl+Super_L+F1")
        self.actions_dict['KEY_TAB'] = lambda key : key_tab(key)
        def kpsplash(key):
              if self.backspace_pressed:
                  os.system("xdotool key Super_L+Shift+Right")
              else:
                  os.system("xdotool key ctrl+Super_L+F2")
        self.actions_dict['KEY_KPSLASH'] = lambda key : kpsplash(key)
        def kpasterisk(key):
              if self.backspace_pressed:
                  os.system("xdotool key Super_L+w")
              else:
                  os.system("xdotool key ctrl+Super_L+F3")    
        self.actions_dict['KEY_KPASTERISK'] = lambda key : kpasterisk(key)

    def parse(self, key):
        print(key.keycode)
        print(key.key_hold == key.keystate)
        if key.keycode in self.actions_dict:
            if key.keycode == 'KEY_BACKSPACE':
                self.actions_dict[key.keycode](key)
            elif key.keystate == key.key_down:
                self.actions_dict[key.keycode](key)
        

try:
    arduino = Serial("/dev/ttyUSB0", 9600, timeout=1)
except SerialException:
    try:
        arduino = Serial("/dev/ttyUSB1", 9600, timeout=1)
    except SerialException:
        print("serial exception")
        muted = False
        unmuted = False



dev = InputDevice(sys.argv[1])
sink1 = sys.argv[2]
sink2 = sys.argv[3]
#dev = InputDevice('/dev/input/event27')
dev.grab()

parser = Parser()
for event in dev.read_loop():
  if event.type == ecodes.EV_KEY:
      key = categorize(event)
      parser.parse(key)



# for event in dev.read_loop():
#   if event.type == ecodes.EV_KEY:
#       key = categorize(event)
#       if key.keycode == "KEY_BACKSPACE":
#           backspace_pressed = True if key.keystate == key.key_down else False
#       if key.keystate == key.key_down:
#           print(key.keycode)
#           if key.keycode == 'KEY_KP6':
#               os.system('xdotool key XF86AudioRaiseVolume')
#           if key.keycode == 'KEY_KP4':
#               os.system('xdotool key XF86AudioLowerVolume')
#           if key.keycode == 'KEY_KP5':
#               os.system('xdotool key XF86AudioMute')
#           if key.keycode == 'KEY_KP1':
#               if backspace_pressed:
#                   arduino.write(buzzer)
#               else:
#                   os.system('xdotool key XF86AudioPrev')
#           if key.keycode == 'KEY_KP2':
#               os.system('xdotool key XF86AudioPlay')
#           if key.keycode == 'KEY_KP3':
#               os.system('xdotool key XF86AudioNext')
#           if key.keycode == 'KEY_KP0':
#               os.system('xdotool key alt alt+shift+Home')
#               if muted:
#                   arduino.write(unmute)
#                   unmuted = True
#                   muted = False
#               elif unmuted:
#                   arduino.write(mute)
#                   unmuted = False
#                   muted = True
#           if key.keycode == 'KEY_KPDOT':
#               print(headphones)
#               if headphones == 1:
#                   os.system('/home/karolh/Desktop/skrypty/makra/movesinks.sh ' + sink1)
#                   headphones = 0
#               else:
#                   os.system('/home/karolh/Desktop/skrypty/makra/movesinks.sh ' + sink2)
#                   headphones = 1
#           if key.keycode == 'KEY_BACKSPACE':
#               pass
#           if key.keycode == 'KEY_KPMINUS':
#               if backspace_pressed:
#                   os.system("xdotool key Super_L+Right")
#               else:
#                   pass
#           if key.keycode == 'KEY_KPPLUS':
#               os.system("xdotool key Super_L+3")
#           if key.keycode == 'KEY_KP7':
#               if backspace_pressed:
#                   os.system("xdotool key Super_L+Shift+Left")
#               else:
#                   os.system("xdotool key ctrl+Super_L+F4")
#           if key.keycode == 'KEY_KP8':
#               if backspace_pressed:
#                   os.system("xdotool key Super_L+Shift+Down")
#               else:
#                   os.system("xdotool key ctrl+Super_L+F5")
#           if key.keycode == 'KEY_KP9':
#               if backspace_pressed:
#                   os.system("xdotool key Super_L+Left")
#               else:
#                   os.system("xdotool key ctrl+Super_L+F6")
#           if key.keycode == 'KEY_TAB':
#               if backspace_pressed:
#                   os.system("xdotool key Super_L+Shift+Up")
#               else:
#                   os.system("xdotool key ctrl+Super_L+F1")
#           if key.keycode == 'KEY_KPSLASH':
#               if backspace_pressed:
#                   os.system("xdotool key Super_L+Shift+Right")
#               else:
#                   os.system("xdotool key ctrl+Super_L+F2")
#           if key.keycode == 'KEY_KPASTERISK':
#               if backspace_pressed:
#                   os.system("xdotool key Super_L+w")
#               else:
#                   os.system("xdotool key ctrl+Super_L+F3")
#              # if windows_max == 0:
#              #     os.system("xdotool key Super_L+Down")
#              #     windows_max = 1
#              # else:
#              #     os.system("xdotool key Super_L+Up")
#              #     windows_max = 0
#              #
