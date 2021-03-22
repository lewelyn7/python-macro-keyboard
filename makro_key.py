#pliki z keycodeami do klawiatury /usr/include/X11
# key.state = key_hold | key_down | key_up
import os
import sys
from serial import Serial, SerialException
from evdev import InputDevice, categorize, ecodes
import queue
import logging
import threading
import time
from datetime import datetime
from pydbus import SystemBus
from gi.repository import GLib



logging.basicConfig()

class ArduinoModule:
    def __init__(self, enable=True):
        self.logger = logging.getLogger(__name__ + ".ArduinoModule")
        self.logger.setLevel(logging.INFO)
        self.enable = enable
        self.connected = False

        self.write_queue = queue.Queue()
        self.send_executor_thread = threading.Thread(target=self.send_executor, daemon=True) 
        self.receiver_thread = threading.Thread(target=self.receiver, daemon=True) 
        # self.receiver_thread = threading.Thread(target=self.receive_executor, daemon=True) 
        self.receiver_queue = queue.Queue(16)
        
        self.send_q_empty_cond = threading.Condition()
        self.connected_cond = threading.Condition()
        self.arduino_lock = threading.Lock()
        
        self.PRECOMMAND = 0
        self.DESK_READY = 1
        self.POSTCOMMAND = 3
        self.MAX_SEND_ATTEMPTS = 15
        self.rcv_buffer = []

        self.send_executor_thread.start()
        self.receiver_thread.start()

        if(self.enable):
            self.connect()
    def connect(self):
        try:
            self.arduino = Serial("/dev/ttyUSB0", 115200, timeout=60)
            self.logger.info("Arduino connected")
            self.connected = True
        except SerialException:
            try:
                self.arduino = Serial("/dev/ttyUSB1", 115200, timeout=60)
                self.logger.info("Arduino connected")
                self.connected = True
            except SerialException:
                self.logger.warning("serial exception")
                self.connected = False
        finally:
            if(self.connected):
                self.connected_cond.acquire()
                self.connected_cond.notify_all()
                self.connected_cond.release()
    def send_str(self, message):
        self.logger.info("sending " + message)
        if not self.enable:
            return False
        if not self.connected:
            self.connect()
            if(not self.connected):
                return False
        self.send_q_empty_cond.acquire()
        self.write_queue.put(message)
        self.send_q_empty_cond.notify()
        self.send_q_empty_cond.release()


    def send_executor(self):
        while(True):
            self.send_q_empty_cond.acquire()
            self.send_q_empty_cond.wait_for(lambda : (not self.write_queue.empty()) and self.enable and self.connected)
            message = self.write_queue.get()
            self.send_q_empty_cond.release()
            
            send_attempts = 0
            for i in range(self.MAX_SEND_ATTEMPTS):
                try:
                    self.logger.info("writing " + message)
                    self.arduino.write(message.encode("UTF-8"))
                    break
                except IOError:
                    self.logger.info("arduino write error")
                    self.connect()


    def receiver(self):
        
        while(True):
            self.connected_cond.acquire()
            self.connected_cond.wait_for(lambda : self.connected ==  True)
            self.connected_cond.release()
            try:
                # if(self.arduino.inWaiting() > 0):
                rcv = self.arduino.readline(64)
                self.logger.debug("READ " + str(rcv))
                str_rcv = rcv.decode("utf-8")
                self.receiver_queue.put(str_rcv, timeout=3)
            except (IOError, queue.Full, UnicodeDecodeError):
                self.logger.warning("arduino read error")
                self.connect()
            # time.sleep(0.01)  


class DeskHandler:


    def __init__(self):
        self.logger = logging.getLogger(__name__ + ".DeskHandler")
        self.logger.setLevel(logging.WARNING)        

        self.arduino = ArduinoModule()
        self.arduino.send_str("init\n")


        self.rcv_callbacks = {}
        self.receiver_thread = threading.Thread(target=self.rcv_actions_handler, daemon=True) 
        self.receiver_thread.start()


        self.invoker_init()
        self.dbus_init()

    def invoker_init(self):
        self.cmds = {}

        def mute():
            self.arduino.send_str('m\n')
        self.cmds['mute'] = mute

        def unmute():
            self.arduino.send_str('u\n')
        self.cmds['unmute'] = unmute

        def notify():
            self.arduino.send_str('n\n')
        self.cmds['notify'] = notify

        def mute_discord():
            self.arduino.send_str('d\n')
        self.cmds['mute_discord'] = mute_discord

    def dbus_init(self):
        def handler(val):
            if val:
                #bye bye
                self.logger.info("bye bye")
                self.arduino.send_str("tsleep\n")
            else:
                #hello
                self.logger.info("wakeup")
                self.arduino.send_str("wakeup\n")


        loop = GLib.MainLoop()
        bus = SystemBus()
        objj = bus.get("org.freedesktop.login1", "/org/freedesktop/login1")
        objj = objj['org.freedesktop.login1.Manager']
        objj.onPrepareForSleep = handler
        self.dbus_thread = threading.Thread(target=loop.run, daemon=True) 
        self.dbus_thread.start()

    def define_callback(self, message, foo):
        self.rcv_callbacks[message] = foo

    def rcv_actions_handler(self):
        while(True):
            mess = self.arduino.receiver_queue.get()
            try:
                self.rcv_callbacks[mess]()
            except KeyError:
                self.logger.warn("No handler for message %s", mess)


    def invoke(self, cmd, payload = None):
        try:
            if payload:
                self.cmds[cmd](payload)
            else:
                self.cmds[cmd]()
        except KeyError:
            self.logger.warn("there is no such command: %s", cmd)


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
        
        # initial state
        self.desk = DeskHandler()
        self.muted = True
        self.unmuted = False
        self.discord_muted = True
        self.headphones = False
        self.windows_max = False
        self.backspace_pressed = False

        #get availbile audio outputs
        sinks = os.popen("pactl list short sinks").read()
        sinks = sinks.split('\n')
        sinks = [ids.split() for ids in sinks]
        headphone_audio_id = 0
        laptop_audio_id = 0
        if 'usb' in sinks[0][1]:
            headphone_audio_id = sinks[0][0]
            laptop_audio_id = sinks[1][0]
        else:
            headphone_audio_id = sinks[1][0]
            laptop_audio_id = sinks[0][0]
        logging.debug(f"headphone audio sink {headphone_audio_id}")
        logging.debug(f"laptop audio sink {laptop_audio_id}")

        #get microphone state
        captureMicStr = os.popen('amixer | grep "Capture.*\[off\]"').read()
        if(captureMicStr == ''):
            self.desk.invoke('unmute')
            self.unmuted = True
            self.muted = False            
        else:
            self.desk.invoke('mute')
            self.unmuted = False
            self.muted = True            
        
        def key_backspace(key):
            if key.keystate == key.key_hold or key.keystate == key.key_down:
                self.backspace_pressed = True
            else:
                self.backspace_pressed = False
        self.actions_dict['KEY_BACKSPACE'] = key_backspace

        self.actions_dict['KEY_KP6'] = lambda key : os.system('xdotool key XF86AudioRaiseVolume')
        self.actions_dict['KEY_KP4'] = lambda key : os.system('xdotool key XF86AudioLowerVolume')
        self.actions_dict['KEY_KP5'] = lambda key : os.system('xdotool key XF86AudioMute')
        def key_kp1(key):
            if self.backspace_pressed:
                os.system('kwriteconfig5 --file kscreenlockerrc  --group Daemon  --key Timeout {time};notify-send \"screen locking set to {time} min\"'.format(time=5))
            else:
                os.system('xdotool key XF86AudioPrev')
        self.actions_dict['KEY_KP1'] = key_kp1
        def key_kp2(key):
            if self.backspace_pressed:
                os.system('kwriteconfig5 --file kscreenlockerrc  --group Daemon  --key Timeout {time};notify-send \"screen locking set to {time} min\"'.format(time=15))                
            else:
                os.system('xdotool key XF86AudioPlay')
        self.actions_dict['KEY_KP2'] = key_kp2
        def key_kp3(key):
            if self.backspace_pressed:
                os.system('kwriteconfig5 --file kscreenlockerrc  --group Daemon  --key Timeout {time};notify-send \"screen locking set to {time} min\"'.format(time=25))
            else:
                os.system('xdotool key XF86AudioNext')
        self.actions_dict['KEY_KP3'] = key_kp3
        
        def key_kp0(key):
            if self.backspace_pressed:
                if self.discord_muted:
                    os.system('xdotool key alt alt+shift+Home')
                    self.desk.invoke('unmute')
                    self.discord_muted = False
                    if self.muted:
                        self.desk.invoke('unmute')
                        self.unmuted = True
                        
                        self.muted = False
                        os.system("amixer set Capture cap")                    
                else:
                    self.discord_muted = True
                    os.system('xdotool key alt alt+shift+Home')
                    self.desk.invoke('mute_discord')
            else:
              
              if self.muted:
                  self.desk.invoke('unmute')
                  self.unmuted = True
                  
                  self.muted = False
                  os.system("amixer set Capture cap")
                  if self.discord_muted:
                      os.system('xdotool key alt alt+shift+Home')
                      self.discord_muted = False
              elif self.unmuted:
                  self.desk.invoke('mute')
                  self.unmuted = False
                  
                  self.muted = True
                  os.system("amixer set Capture nocap")
                  if not self.discord_muted:
                      os.system('xdotool key alt alt+shift+Home')
                      self.discord_muted = True
        self.actions_dict['KEY_KP0'] = key_kp0
        
        def move_audio_sinks(dest_audio_sink):
            streams = os.popen("pactl list short sink-inputs").read()
            streams = streams.split('\n')
            streams = [stream.split() for stream in streams][:-1]
            streams = filter(lambda s: (s[1] == headphone_audio_id or s[1] == laptop_audio_id), streams)
            for stream in streams:
                os.system(f"pactl move-sink-input {stream[0]} {dest_audio_sink}")

        def kp_dot(key):
            # print(self.headphones)
            if self.headphones == 1:
                move_audio_sinks(laptop_audio_id)
                # os.system('/home/karolh/Desktop/skrypty/makra/movesinks.sh ' + sink1)
                self.headphones = 0
            else:
                move_audio_sinks(headphone_audio_id)
                # os.system('/home/karolh/Desktop/skrypty/makra/movesinks.sh ' + sink2)
                self.headphones = 1
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

if __name__ == "__main__":
    
    dev = InputDevice(sys.argv[1])
    sink1 = sys.argv[2]
    sink2 = sys.argv[3]
    dev.grab()

    #parser = HomeParser()
    parser = Parser(True)

    for event in dev.read_loop():
        if event.type == ecodes.EV_KEY:
            key = categorize(event)
            parser.parse(key)

