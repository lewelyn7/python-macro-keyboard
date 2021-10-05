import threading
from serial import Serial, SerialException
import queue
import time
import logging
class ArduinoModule:
    
    def __init__(self, enable=True):
        self.logger = logging.getLogger(__name__).getChild("arduino_module")
        self.logger.setLevel(logging.WARNING)
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
        self.connected = False
        attempt_counter = 0
        while not self.connected:
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
                    self.logger.warning(f"retrying in 3 seconds")
                    time.sleep(3)
            except (OSError, FileNotFoundError) as e:
                self.logger.error(f"OS ERROR {repr(e)}")
                self.logger.error(f"retrying in 3 seconds")
                time.sleep(3)
            finally:
                attempt_counter += 1
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
                except (IOError, OSError):
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
            except (IOError, queue.Full, UnicodeDecodeError, OSError):
                self.logger.warning("arduino read error")
                self.connect()
            # time.sleep(0.01)  