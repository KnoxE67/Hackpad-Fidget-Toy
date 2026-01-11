import board
from kmk.kmk_keyboard import KMKKeyboard
from kmk.scanners.keypad import KeysScanner
from kmk.keys import KC
from kmk.modules.macros import Macros
from kmk.modules.encoder import EncoderHandler
from kmk.extensions.display import Display, TextEntry, BarEntry
from kmk.extensions.display.ssd1306 import SSD1306

keyboard = KMKKeyboard()
macros = Macros()
keyboard.modules.append(macros)

# 1. Rotary Encoder Setup (EC11E)
encoder_handler = EncoderHandler()
keyboard.modules.append(encoder_handler)
encoder_handler.pins = ((board.D3, board.D4, board.A3, False),)
encoder_handler.divisor = 4 

# 2. OLED Display Setup
i2c_bus = board.I2C() 
display_driver = SSD1306(i2c=i2c_bus, device_address=0x3C)

header_text = TextEntry(x=0, y=0, text='HACKPAD-FIDGET')
status_text = TextEntry(x=0, y=10, text='MODE: MACRO')

# Volume Bar: x=0, y=22, width=128, height=8
volume_bar = BarEntry(x=0, y=22, width=128, height=8, value=50) 

display_setup = Display(
    display_driver=display_driver,
    entries=[header_text, status_text, volume_bar]
)
keyboard.extensions.append(display_setup)

# 3. Keypad Matrix (SW_1 to SW_6)
PINS = [board.D0, board.D1, board.D2, board.D26, board.D27, board.D28]
keyboard.matrix = KeysScanner(pins=PINS, value_when_pressed=False)

# 4. Keymap (Mac Layout)
keyboard.keymap = [[
    KC.ESC,           # SW_1
    KC.F4,            # SW_2
    KC.DELETE,        # SW_3
    KC.LCMD(KC.C),    # SW_4
    KC.LCMD(KC.V),    # SW_5
    KC.ENTER,         # SW_6
]]

# 5. Encoder Mapping
encoder_handler.map = [((KC.VOLU, KC.VOLD, KC.MUTE),)]

# 6. Logic to update the Volume Bar and Text
class HackpadModule:
    def __init__(self):
        self.vol_level = 50

    def on_runtime_enable(self, keyboard): pass
    def on_runtime_disable(self, keyboard): pass
    def before_matrix_scan(self, keyboard): pass
    def after_matrix_scan(self, keyboard): pass
    def before_hid_send(self, keyboard): pass
    def after_hid_send(self, keyboard): pass
    def on_powersave_enable(self, keyboard): pass
    def on_powersave_disable(self, keyboard): pass

    def after_key_handler(self, keyboard, key, is_pressed):
        if is_pressed:
            if key == KC.LCMD(KC.C): status_text.text = "COPYING..."
            elif key == KC.LCMD(KC.V): status_text.text = "PASTING..."
            elif key == KC.F4: status_text.text = "SEARCHING..."
            elif key == KC.DELETE: status_text.text = "DELETING..."
            elif key == KC.MUTE: status_text.text = "MUTE TOGGLE"
            elif key == KC.ESC: status_text.text = "ESCAPE"
            elif key == KC.ENTER: status_text.text = "ENTER"
            
            # Volume Logic
            if key == KC.VOLU:
                self.vol_level = min(100, self.vol_level + 5)
                volume_bar.value = self.vol_level
            elif key == KC.VOLD:
                self.vol_level = max(0, self.vol_level - 5)
                volume_bar.value = self.vol_level
        else:
            # Returns to default text when key is released
            status_text.text = "MODE: MACRO"

keyboard.modules.append(HackpadModule())

if __name__ == '__main__':
    keyboard.go()