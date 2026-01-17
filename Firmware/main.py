import board
import busio
import displayio
import terminalio
import microcontroller
import adafruit_displayio_ssd1306
import time
import sys # For reading terminal input

from kmk.extensions.media_keys import MediaKeys
from adafruit_display_text import label
from kmk.kmk_keyboard import KMKKeyboard
from kmk.scanners.keypad import KeysScanner
from kmk.keys import KC
from kmk.modules.macros import Macros
from kmk.modules.encoder import EncoderHandler

# --- 1. OLED Setup ---
displayio.release_displays()
i2c = busio.I2C(microcontroller.pin.GPIO7, microcontroller.pin.GPIO6)
display_bus = displayio.I2CDisplay(i2c, device_address=0x3C)
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=32)

splash = displayio.Group()
display.root_group = splash

header_lbl = label.Label(terminalio.FONT, text="Knoxs-Hackpad", x=0, y=5)
status_lbl = label.Label(terminalio.FONT, text="MODE: ACRO", x=0, y=16)
vol_lbl = label.Label(terminalio.FONT, text="VOL: [|||||-----] 50%", x=0, y=27)

splash.append(header_lbl)
splash.append(status_lbl)
splash.append(vol_lbl)

def update_oled_vol(level, muted):
    if muted:
        vol_lbl.text = "VOL: [ MUTED X ]"
    else:
        filled = level // 10
        bar = "|" * filled + "-" * (10 - filled)
        vol_lbl.text = f"VOL: [{bar}] {level}%"

# --- 2. Keyboard Setup ---
keyboard = KMKKeyboard()
macros = Macros()
keyboard.modules.append(macros)
keyboard.extensions.append(MediaKeys())

# --- 3. Encoder Setup ---
encoder_handler = EncoderHandler()
keyboard.modules.append(encoder_handler)
encoder_handler.pins = ((microcontroller.pin.GPIO4, microcontroller.pin.GPIO3, microcontroller.pin.GPIO29, False),)
encoder_handler.divisor = 4

# --- 4. Matrix Setup ---
PINS = [
    microcontroller.pin.GPIO0, microcontroller.pin.GPIO1, microcontroller.pin.GPIO2, 
    microcontroller.pin.GPIO26, microcontroller.pin.GPIO27, microcontroller.pin.GPIO28
]
keyboard.matrix = KeysScanner(pins=PINS, value_when_pressed=False)

# --- 5. Keymap ---
keyboard.keymap = [[
    KC.ESC, KC.F4, KC.DELETE,
    KC.LCMD(KC.C), KC.LCMD(KC.V), KC.ENTER,
]]
encoder_handler.map = [((KC.VOLU, KC.VOLD, KC.MUTE),)]

# --- 6. Custom Logic Module ---
class HackpadModule:
    def __init__(self):
        self.vol_level = 50
        self.is_muted = False
        self.last_activity = time.monotonic()
        self.is_sleeping = False
        self.timeout = 300 # 5 Minutes

    def wake(self):
        if self.is_sleeping:
            display.wake()
            self.is_sleeping = False
            print(">> Display Waking Up")
        self.last_activity = time.monotonic()

    def before_matrix_scan(self, keyboard):
        # Auto-sleep after timeout
        if not self.is_sleeping and (time.monotonic() - self.last_activity > self.timeout):
            display.sleep()
            self.is_sleeping = True
            print(">> Timeout: Display Sleeping")

    def on_runtime_enable(self, keyboard): 
        update_oled_vol(self.vol_level, self.is_muted)
        print(">> Hackpad Active. Type 's' in terminal to test Sleep.")

    def deinit(self, keyboard): pass
    def on_runtime_disable(self, keyboard): pass
    def during_bootup(self, keyboard): pass
    def after_matrix_scan(self, keyboard): pass
    def before_hid_send(self, keyboard): pass
    def after_hid_send(self, keyboard): pass

    def after_key_handler(self, keyboard, key, is_pressed):
        if is_pressed:
            self.wake()
            k = str(key)
            
            # Simple status change logic
            if "LCMD" in k and "C" in k: status_lbl.text = "COPYING..."
            elif "LCMD" in k and "V" in k: status_lbl.text = "PASTING..."
            elif "F4" in k: status_lbl.text = "SEARCHING..."
            elif "ENTER" in k: status_lbl.text = "ENTERING..."
            elif "DELETE" in k: status_lbl.text = "DELETING..."
            elif "ESC" in k: status_lbl.text = "ESCAPING..."
            
            if key == KC.VOLU or "VOLU" in k:
                self.is_muted = False
                self.vol_level = min(100, self.vol_level + 5)
            elif key == KC.VOLD or "VOLD" in k:
                self.is_muted = False
                self.vol_level = max(0, self.vol_level - 5)
            elif key == KC.MUTE or "MUTE" in k:
                self.is_muted = not self.is_muted
            
            update_oled_vol(self.vol_level, self.is_muted)
            print(f"Action: {status_lbl.text} | Vol: {self.vol_level}%")
        else:
            status_lbl.text = "MODE: ACRO"

keyboard.modules.append(HackpadModule())

if __name__ == '__main__':
    keyboard.go()