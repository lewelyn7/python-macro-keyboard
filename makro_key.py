#pliki z keycodeami do klawiatury /usr/include/X11
# key.state = key_hold | key_down | key_up
import os
import sys
from evdev import InputDevice, categorize, ecodes
import queue
import logging
import time
import logging.config
from datetime import datetime
from MQTThandler import MQTThandler
from desk_handler import DeskHandler
from unittest.mock import Mock
from audio_manager import AudioManager
from MQTThandler import MQTThandler








class AbstractParser:
    def __init__(self):
        self.actions_dict = {}        
        self.logger = logging.getLogger(__name__ + ".Parser")
        # self.logger.setLevel(logging.DEBUG)
    def parse(self, key):
        self.logger.info("\n")
        self.logger.info(key.keycode)
        self.logger.debug(key.key_hold == key.keystate)
        if key.keycode in self.actions_dict:
            if key.keycode == 'KEY_BACKSPACE':
                self.actions_dict[key.keycode](key)
            elif key.keystate == key.key_down:
                self.actions_dict[key.keycode](key)

class DigikamParser(AbstractParser):
    """
        0-5 : giving stars to photos
        7,8,9,- : giving flags to photos
        + : arrow left
        Enter : arrow right

    Args:
        AbstractParser ([type]): [description]
    """
    def __init__(self):
        super().__init__()
        self.actions_dict['KEY_KP0'] = lambda key : os.system('xdotool key ctrl+0')
        self.actions_dict['KEY_KP1'] = lambda key : os.system('xdotool key ctrl+1')
        self.actions_dict['KEY_KP2'] = lambda key : os.system('xdotool key ctrl+2')
        self.actions_dict['KEY_KP3'] = lambda key : os.system('xdotool key ctrl+3')
        self.actions_dict['KEY_KP4'] = lambda key : os.system('xdotool key ctrl+4')
        self.actions_dict['KEY_KP5'] = lambda key : os.system('xdotool key ctrl+5')

        self.actions_dict['KEY_KP7'] = lambda key : os.system('xdotool key alt+0')
        self.actions_dict['KEY_KP8'] = lambda key : os.system('xdotool key alt+1')
        self.actions_dict['KEY_KP9'] = lambda key : os.system('xdotool key alt+2')
        self.actions_dict['KEY_KPMINUS'] = lambda key : os.system('xdotool key alt+3')
        
        self.actions_dict['KEY_KPPLUS'] = lambda key : os.system('xdotool key Left')
        self.actions_dict['KEY_ENTER'] = lambda key : os.system('xdotool key Right')


class Parser(AbstractParser):
    def __init__(self, ardu):
        super().__init__()
        
        self.logger.setLevel(logging.DEBUG)

        # initial state
        self.desk = DeskHandler()
        # self.desk = Mock(spec=DeskHandler)
        self.muted = True
        self.unmuted = False
        self.discord_muted = True
        self.headphones = False
        self.windows_max = False
        self.backspace_pressed = False
        self.mqtt_handler = MQTThandler()


        self.audio_manager = AudioManager(self.desk)

        
        def key_backspace(key):
            if key.keystate == key.key_hold or key.keystate == key.key_down:
                self.backspace_pressed = True
            else:
                self.backspace_pressed = False
        self.actions_dict['KEY_BACKSPACE'] = key_backspace

        self.actions_dict['KEY_KP6'] = lambda key : self.audio_manager.volume_up()
        self.actions_dict['KEY_KP4'] = lambda key : self.audio_manager.volume_down()
        self.actions_dict['KEY_KP5'] = lambda key : self.audio_manager.volume_toggle_mute()
        def key_kp1(key):
            if self.backspace_pressed:
                os.system('kwriteconfig5 --file kscreenlockerrc  --group Daemon  --key Timeout {time};notify-send \"screen locking set to {time} min\"'.format(time=5))
            else:
               self.audio_manager.audio_prev()
        self.actions_dict['KEY_KP1'] = key_kp1
        def key_kp2(key):
            if self.backspace_pressed:
                os.system('kwriteconfig5 --file kscreenlockerrc  --group Daemon  --key Timeout {time};notify-send \"screen locking set to {time} min\"'.format(time=15))                
            else:
                self.audio_manager.audio_play()
        self.actions_dict['KEY_KP2'] = key_kp2
        def key_kp3(key):
            if self.backspace_pressed:
                os.system('kwriteconfig5 --file kscreenlockerrc  --group Daemon  --key Timeout {time};notify-send \"screen locking set to {time} min\"'.format(time=25))
            else:
                self.audio_manager.audio_next()
        self.actions_dict['KEY_KP3'] = key_kp3
        
        def key_kp0(key):
            os.system('xdotool key alt+mu')
            state = None
            if self.backspace_pressed:
                state = self.audio_manager.toggle_mic_mute()
            else:
                state = self.audio_manager.toggle_mic_mute()
            if state == True:
                self.desk.invoke("mute")
                self.mqtt_handler.send_mic_state(mute=True)
            else:
                self.desk.invoke("unmute")
                self.mqtt_handler.send_mic_state(mute=False)
        self.actions_dict['KEY_KP0'] = key_kp0
        

        def kp_dot(key):
            self.audio_manager.toggle_audio_output()
        self.actions_dict['KEY_KPDOT'] = kp_dot
        
        def kp_minus(key):
              if self.backspace_pressed:
                  os.system("xdotool key Super_L+Right")
              else:
                  pass            
        self.actions_dict['KEY_KPMINUS'] = kp_minus

        self.actions_dict['KEY_KPPLUS'] = lambda key : os.system("xdotool key Super_L+3")
        
        def kp7(key):
              if self.backspace_pressed:
                  os.system("xdotool key Super_L+Shift+Left")
              else:
                  os.system("xdotool key ctrl+Super_L+F8")
        self.actions_dict['KEY_KP7'] = kp7 
        
        def kp8(key):
              if self.backspace_pressed:
                  os.system("xdotool key Super_L+Shift+Down")
              else:
                  os.system("xdotool key ctrl+Super_L+F5")
        self.actions_dict['KEY_KP8'] = kp8
        
        def kp9(key):
              if self.backspace_pressed:
                  os.system("xdotool key Super_L+Left")
              else:
                  os.system("xdotool key ctrl+Super_L+F6")
        self.actions_dict['KEY_KP9'] = kp9
        
        def key_tab(key):
              if self.backspace_pressed:
                  os.system("xdotool key Super_L+Alt+F10")
              else:
                  os.system("xdotool key ctrl+Super_L+F1")
        self.actions_dict['KEY_TAB'] = key_tab
        def kpsplash(key):
              if self.backspace_pressed:
                  os.system("xdotool key Super_L+Alt+F9")
              else:
                  os.system("xdotool key ctrl+Super_L+F2")
        self.actions_dict['KEY_KPSLASH'] = kpsplash
        
        def kpasterisk(key):
              if self.backspace_pressed:
                  os.system("xdotool key Super_L+w")
              else:
                  os.system("xdotool key ctrl+Super_L+F3")    
        self.actions_dict['KEY_KPASTERISK'] = kpasterisk




class HomeParser(Parser):
    def __init__(self):
        super().__init__(True)
        self.actions_dict['KEY_NUMLOCK'] =  self.actions_dict['KEY_TAB']# key_tab for home version


def __tests():
    desk = DeskHandler()
    desk.mute()
    desk.unmute()
    desk.notify()



def find_keypad():
    for i in range(5):
        devices_lines = os.popen("cat /proc/bus/input/devices").read().split("\n")
        for i, line in enumerate(devices_lines):
            if line.endswith("Keypad\""):
                return(devices_lines[i+4].split()[-1])
        
        time.sleep(3)


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.WARNING)
    log_file_handler = logging.FileHandler("makra/logs.log")
    log_file_handler.setLevel(logging.ERROR)
    formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s: %(message)s')
    stream_handler.setFormatter(formatter)
    log_file_handler.setFormatter(formatter)
    logging.basicConfig(handlers=[stream_handler, log_file_handler], force=True)

    

    #parser = HomeParser()
    parser = Parser(True)
    #TODO its just a workaround
    while True:

        dev = InputDevice("/dev/input/" + find_keypad())
        dev.grab()

        try:
            for event in dev.read_loop():
                if event.type == ecodes.EV_KEY:
                    key = categorize(event)
                    parser.parse(key)
        except OSError:
            logger.warning("event dev loop broken")
            logger.warning("retry in 2s")
            time.sleep(2)

