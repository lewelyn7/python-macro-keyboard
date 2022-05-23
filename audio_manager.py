import os
import pulsectl
import logging
class AudioManager:

    mic_muted = False
    headphones = False

    def __init__(self, desk_handler):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.desk_handler = desk_handler
        self.sync_microphone_state()
        self._sync_audio_outputs() #workaround
        self._sync_audio_sink_inputs()
        

    def _sync_audio_sink_inputs(self):
        self.pulse = pulsectl.Pulse("makro_keyboard")
        self._update_audio_sink_inputs()

    def _update_audio_sink_inputs(self):
        self.sink_inputs = { i.name:i  for i in self.pulse.sink_input_list()}

    def _set_sink_input_volume(self, name, volume):
        self.pulse.sink_input_volume_set(self.sink_inputs[name].index, volume)
        
    def sync_microphone_state(self):
        #get microphone state
        captureMicStr = os.popen('amixer | grep "Capture.*\[off\]"').read()
        if(captureMicStr == ''):
            self.unmute_mic()
        else:
            self.mute_mic()

    def _sync_audio_outputs(self):
        #get availbile audio outputs
        sinks = os.popen("pactl list short sinks").read()
        sinks = sinks.split('\n')
        sinks = [ids.split() for ids in sinks]
        headphone_audio_id = 0
        laptop_audio_id = 0
        if 'USB' in sinks[0][1]:
            headphone_audio_id = sinks[0][0]
            laptop_audio_id = sinks[1][0]
        else:
            headphone_audio_id = sinks[1][0]
            laptop_audio_id = sinks[0][0]

        self.logger.debug(f"headphone audio sink {headphone_audio_id}")
        self.logger.debug(f"laptop audio sink {laptop_audio_id}")
        self.headphone_audio_id = headphone_audio_id
        self.laptop_audio_id = laptop_audio_id



    def _set_audio(self, num):
        resp = os.popen(f"pactl set-default-sink {num}").read()
        if resp.startswith("Failure"):
            self.logger.debug("failure redetecting usb devices")
            self._sync_audio_outputs()
            resp = os.popen(f"pactl set-default-sink {num}").read()
            if resp.startswith("Failure"):
                self.logger.warning("couldnt switch audio devices")

    def _move_audio_sinks(self, dest_audio_sink):
        streams = os.popen("pactl list short sink-inputs").read()
        streams = streams.split('\n')
        streams = [stream.split() for stream in streams][:-1]
        streams = filter(lambda s: (s[1] == self.headphone_audio_id or s[1] == self.laptop_audio_id), streams)
        for stream in streams:
            os.system(f"pactl move-sink-input {stream[0]} {dest_audio_sink}")



    def volume_down(self):
        os.system('xdotool key XF86AudioLowerVolume')
    def volume_up(self):
        os.system('xdotool key XF86AudioRaiseVolume')

    def audio_prev(self):
         os.system('xdotool key XF86AudioPrev')
    def audio_next(self):
        os.system('xdotool key XF86AudioNext')
    def audio_play(self):
        os.system('xdotool key XF86AudioPlay')

    def mute_mic(self):
        self.mic_muted = True
        self.desk_handler.invoke('mute')
        os.system("amixer set Capture nocap")
    
    def unmute_mic(self):
        self.mic_muted = False
        self.desk_handler.invoke('unmute')
        os.system("amixer set Capture cap")
    
    def toggle_mic_mute(self):
        # os.system('xdotool key Shift_R+Control_R+y')
        if self.mic_muted:
            self.unmute_mic()
            return False
        else:
            self.mute_mic()
            return True

    def volume_toggle_mute(self):
        os.system('xdotool key XF86AudioMute')

    def to_headphones(self):
        self.headphones = True
        self._move_audio_sinks(self.headphone_audio_id)
        self._set_audio(self.headphone_audio_id)
        os.system('notify-send "moving to headphone audio"')

    def to_speakers(self):
        self.headphones = False
        self._move_audio_sinks(self.laptop_audio_id)
        self._set_audio(self.laptop_audio_id)
        os.system('notify-send "moving to built-in audio"')

    def toggle_audio_output(self):
        if self.headphones:
            self.to_speakers()
        else:
            self.to_headphones()