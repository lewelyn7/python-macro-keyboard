## Python macro keyboard

Simple script that can intercept keyboard events and assign them specific actions. Can be used to create macro keyboard from a numeric keypad.

Script is highly customizable and can perform wide variety of actions. In my version I added handling of:
 * Communication with my [DIY Arduino desk ambilight controller](https://github.com/lewelyn7/IOT-desk-controller)
 * Listening for `PrepareToSleep` and `WakeUp` events via KDE D-Bus
 * Control of audio output devices via `amixer`

## Usage

Script listens for keyboard events and pass them to `Parser` class through `parse` method, that run proper action based on which key is pressed or released. If you want to create different setups for different applications for example, just create several `Parser` classes that implements `parse(self, key)` method. Actions are organized as a dictionary of strings as keys and functions as values. 

```python
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
```
I'm also using two utility classes to encapsulate and handle communication with Arduino: `DeskHandler` and `ArduinoHandler`.

