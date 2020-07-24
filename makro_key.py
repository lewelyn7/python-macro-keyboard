#pliki z keycodeami do klawiatury /usr/include/X11

import os
import sys
from serial import Serial, SerialException
from evdev import InputDevice, categorize, ecodes


# initial state
muted = True
unmuted = False
headphones = False
windows_max = False
backspace_pressed = False

try:
    arduino = Serial("/dev/ttyUSB0", 9600, timeout=1)
except SerialException:
    try:
        arduino = Serial("/dev/ttyUSB1", 9600, timeout=1)
    except SerialException:
        print("serial exception")
        muted = False
        unmuted = False

#presetet strings to be sent by serial
mute = "m".encode("UTF-8")
unmute = "u".encode("UTF-8")
buzzer = "b".encode("UTF-8")

dev = InputDevice(sys.argv[1])
sink1 = sys.argv[2]
sink2 = sys.argv[3]
#dev = InputDevice('/dev/input/event27')
dev.grab()



for event in dev.read_loop():
  if event.type == ecodes.EV_KEY:
      key = categorize(event)
      if key.keycode == "KEY_BACKSPACE":
          backspace_pressed = True if key.keystate == key.key_down else False
      if key.keystate == key.key_down:
          print(key.keycode)
          if key.keycode == 'KEY_KP6':
              os.system('xdotool key XF86AudioRaiseVolume')
          if key.keycode == 'KEY_KP4':
              os.system('xdotool key XF86AudioLowerVolume')
          if key.keycode == 'KEY_KP5':
              os.system('xdotool key XF86AudioMute')
          if key.keycode == 'KEY_KP1':
              if backspace_pressed:
                  arduino.write(buzzer)
              else:
                  os.system('xdotool key XF86AudioPrev')
          if key.keycode == 'KEY_KP2':
              os.system('xdotool key XF86AudioPlay')
          if key.keycode == 'KEY_KP3':
              os.system('xdotool key XF86AudioNext')
          if key.keycode == 'KEY_KP0':
              os.system('xdotool key alt alt+shift+Home')
              if muted:
                  arduino.write(unmute)
                  unmuted = True
                  muted = False
              elif unmuted:
                  arduino.write(mute)
                  unmuted = False
                  muted = True
          if key.keycode == 'KEY_KPDOT':
              print(headphones)
              if headphones == 1:
                  os.system('/home/karolh/Desktop/skrypty/makra/movesinks.sh ' + sink1)
                  headphones = 0
              else:
                  os.system('/home/karolh/Desktop/skrypty/makra/movesinks.sh ' + sink2)
                  headphones = 1
          if key.keycode == 'KEY_BACKSPACE':
              pass
          if key.keycode == 'KEY_KPMINUS':
              if backspace_pressed:
                  os.system("xdotool key Super_L+Right")
              else:
                  pass
          if key.keycode == 'KEY_KPPLUS':
              os.system("xdotool key Super_L+3")
          if key.keycode == 'KEY_KP7':
              if backspace_pressed:
                  os.system("xdotool key Super_L+Shift+Left")
              else:
                  os.system("xdotool key ctrl+Super_L+F4")
          if key.keycode == 'KEY_KP8':
              if backspace_pressed:
                  os.system("xdotool key Super_L+Shift+Down")
              else:
                  os.system("xdotool key ctrl+Super_L+F5")
          if key.keycode == 'KEY_KP9':
              if backspace_pressed:
                  os.system("xdotool key Super_L+Left")
              else:
                  os.system("xdotool key ctrl+Super_L+F6")
          if key.keycode == 'KEY_TAB':
              if backspace_pressed:
                  os.system("xdotool key Super_L+Shift+Up")
              else:
                  os.system("xdotool key ctrl+Super_L+F1")
          if key.keycode == 'KEY_KPSLASH':
              if backspace_pressed:
                  os.system("xdotool key Super_L+Shift+Right")
              else:
                  os.system("xdotool key ctrl+Super_L+F2")
          if key.keycode == 'KEY_KPASTERISK':
              if backspace_pressed:
                  os.system("xdotool key Super_L+w")
              else:
                  os.system("xdotool key ctrl+Super_L+F3")
             # if windows_max == 0:
             #     os.system("xdotool key Super_L+Down")
             #     windows_max = 1
             # else:
             #     os.system("xdotool key Super_L+Up")
             #     windows_max = 0
             #
