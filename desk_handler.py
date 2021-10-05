from arduino_module import ArduinoModule
import threading
from gi.repository import GLib

from pydbus import SystemBus
import logging

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
                
                if not mess.strip().isnumeric():
                    self.rcv_callbacks[mess]()
            except KeyError:
                self.logger.info("No handler for message %s", mess)


    def invoke(self, cmd, payload = None):
        try:
            if payload:
                self.cmds[cmd](payload)
            else:
                self.cmds[cmd]()
        except KeyError:
            self.logger.warn("there is no such command: %s", cmd)
