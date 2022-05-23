import paho.mqtt.client as mqtt
import logging
import threading
import time
class MQTThandler:

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.topics = [
            "/laptop/audio/spotify/vol",
            "/laptop/audio/discord/vol",
            "/laptop/audio/web/vol",
            "/laptop/audio/all/vol"
            "/laptop/audio/mic/rec"
        ]
        self.client_id = "laptop"


        self.disconnected = (False, None)
        self.client = mqtt.Client(client_id=self.client_id)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        
        self.logger.info("MQTT connecting...")
        self.client.connect("192.168.1.129", 1883, 60)
        self.mqtt_loop_thread = threading.Thread(target=self.loop, daemon=True) 
        self.mqtt_loop_thread.start()


    def on_connect(self, client, userdata, flags, rc):
        self.logger.info("connected to MQTT broker")
        self.logger.info("Subscribing")
        for topic in self.topics:
            client.subscribe(topic)

    def on_disconnect(self, client, userdata, rc):
        self.disconnected = True, rc
        self.logger.warning("disconnected from MQTT broker")

    def on_message(self, client, userdata, msg):
        self.logger.info(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))

    def loop(self):
        while True:
            if self.disconnected[0] == False:
                self.client.loop_forever()
            time.sleep(5)
            self.logger.warning("mqtt disconnected")

    def on_audio_mute(mosq, obj, msg):
        # This callback will only be called for messages with topics that match
        # $SYS/broker/messages/#
        print("MESSAGES: " + msg.topic + " " + str(msg.qos) + " " + str(msg.payload))

    def send_mic_state(self, mute):
        if mute == True:
            self.client.publish("/laptop/audio/mic/rec", "OFF")
        elif mute == False:
            self.client.publish("/laptop/audio/mic/rec", "ON")