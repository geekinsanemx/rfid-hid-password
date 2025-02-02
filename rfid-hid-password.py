import board
import digitalio
import time
from mfrc522 import MFRC522
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode

# Define SPI pins for RP2040-Zero
sck = board.GP2
mosi = board.GP3
miso = board.GP4
cs = board.GP0
rst = board.GP1

# Initialize MFRC522
rfid = MFRC522(sck, mosi, miso, rst, cs)

# Initialize USB HID Keyboard
kbd = Keyboard(usb_hid.devices)

# Initialize LEDs
red_led = digitalio.DigitalInOut(board.GP5)
red_led.direction = digitalio.Direction.OUTPUT
green_led = digitalio.DigitalInOut(board.GP6)
green_led.direction = digitalio.Direction.OUTPUT
blue_led = digitalio.DigitalInOut(board.GP7)
blue_led.direction = digitalio.Direction.OUTPUT

# Turn off LEDs initially
red_led.value = False
green_led.value = False
blue_led.value = False

# Mapping of printable ASCII characters to Keycode
ascii_to_keycode = {
    # Space
    ' ': Keycode.SPACE,

    # Digits
    '0': Keycode.ZERO,
    '1': Keycode.ONE,
    '2': Keycode.TWO,
    '3': Keycode.THREE,
    '4': Keycode.FOUR,
    '5': Keycode.FIVE,
    '6': Keycode.SIX,
    '7': Keycode.SEVEN,
    '8': Keycode.EIGHT,
    '9': Keycode.NINE,

    # Uppercase letters
    'A': Keycode.A,
    'B': Keycode.B,
    'C': Keycode.C,
    'D': Keycode.D,
    'E': Keycode.E,
    'F': Keycode.F,
    'G': Keycode.G,
    'H': Keycode.H,
    'I': Keycode.I,
    'J': Keycode.J,
    'K': Keycode.K,
    'L': Keycode.L,
    'M': Keycode.M,
    'N': Keycode.N,
    'O': Keycode.O,
    'P': Keycode.P,
    'Q': Keycode.Q,
    'R': Keycode.R,
    'S': Keycode.S,
    'T': Keycode.T,
    'U': Keycode.U,
    'V': Keycode.V,
    'W': Keycode.W,
    'X': Keycode.X,
    'Y': Keycode.Y,
    'Z': Keycode.Z,

    # Lowercase letters (same as uppercase, but you can handle case in your code)
    'a': Keycode.A,
    'b': Keycode.B,
    'c': Keycode.C,
    'd': Keycode.D,
    'e': Keycode.E,
    'f': Keycode.F,
    'g': Keycode.G,
    'h': Keycode.H,
    'i': Keycode.I,
    'j': Keycode.J,
    'k': Keycode.K,
    'l': Keycode.L,
    'm': Keycode.M,
    'n': Keycode.N,
    'o': Keycode.O,
    'p': Keycode.P,
    'q': Keycode.Q,
    'r': Keycode.R,
    's': Keycode.S,
    't': Keycode.T,
    'u': Keycode.U,
    'v': Keycode.V,
    'w': Keycode.W,
    'x': Keycode.X,
    'y': Keycode.Y,
    'z': Keycode.Z,

    # Special characters
    '!': Keycode.ONE,  # Shift + 1
    '"': Keycode.QUOTE,  # Shift + '
    '#': Keycode.THREE,  # Shift + 3
    '$': Keycode.FOUR,  # Shift + 4
    '%': Keycode.FIVE,  # Shift + 5
    '&': Keycode.SEVEN,  # Shift + 7
    "'": Keycode.QUOTE,
    '(': Keycode.NINE,  # Shift + 9
    ')': Keycode.ZERO,  # Shift + 0
    '*': Keycode.EIGHT,  # Shift + 8
    '+': Keycode.EQUALS,  # Shift + =
    ',': Keycode.COMMA,
    '-': Keycode.MINUS,
    '.': Keycode.PERIOD,
    '/': Keycode.FORWARD_SLASH,
    ':': Keycode.SEMICOLON,  # Shift + ;
    ';': Keycode.SEMICOLON,
    '<': Keycode.COMMA,  # Shift + ,
    '=': Keycode.EQUALS,
    '>': Keycode.PERIOD,  # Shift + .
    '?': Keycode.FORWARD_SLASH,  # Shift + /
    '@': Keycode.TWO,  # Shift + 2
    '[': Keycode.LEFT_BRACKET,
    '\\': Keycode.BACKSLASH,
    ']': Keycode.RIGHT_BRACKET,
    '^': Keycode.SIX,  # Shift + 6
    '_': Keycode.MINUS,  # Shift + -
    '`': Keycode.GRAVE_ACCENT,
    '{': Keycode.LEFT_BRACKET,  # Shift + [
    '|': Keycode.BACKSLASH,  # Shift + \
    '}': Keycode.RIGHT_BRACKET,  # Shift + ]
    '~': Keycode.GRAVE_ACCENT,  # Shift + `
}

def type_string(text):
    """Type out a string as keyboard input."""
    for char in text:
        if char in ascii_to_keycode:
            keycode = ascii_to_keycode[char]
            
            # Handle Shift key for uppercase letters and special characters
            if char.isupper() or char in '!@#$%^&*()_+{}|:"<>?~':
                kbd.press(Keycode.SHIFT)  # Press Shift key
            
            kbd.press(keycode)  # Press the key
            kbd.release_all()   # Release all keys
        else:
            print(f"Unsupported character: {char}")

# Load default key from JSON file
def load_default_key(file_path):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            return data.get('default_key', [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF])
        
    except:
        print(f"File {file_path} not found or invalid. Using default key.")
        return [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
    
# Path to the JSON file containing the default key
default_key_file = 'default_key.json'
default_key = load_default_key(default_key_file)

# Main loop
print("Waiting for RFID/NFC card...")
while True:
    # Turn off LEDs at the start of each loop
    red_led.value = False
    green_led.value = False
    blue_led.value = False

    # Scan for cards
    (status, tag_type) = rfid.request(rfid.REQIDL)
    if status == rfid.OK:
        print("Card detected!")
        blue_led.value = True
        
        # Get the UID of the card
        (status, raw_uid) = rfid.SelectTagSN()
        
        if status == rfid.OK:
            uid_hex = ''.join('{:02X}'.format(x) for x in raw_uid)
            
            print("Card UID:", uid_hex)
            print("  - tag type: 0x%02x" % tag_type)

            if rfid.IsNTAG():
                print("Got NTAG{}".format(rfid.NTAG))
                
                data = rfid.read(8)
                print(list(data))

                if status == rfid.OK and data is not None:
                    password = ''.join(chr(byte) for byte in data if byte != 0)

                    if list(data) == [0] * 16:  # Check if the block is empty
                        print("Password empty. Typing UID instead.")
                        print(uid_hex)
                        type_string(uid_hex)
                        green_led.value = True
                    elif password.strip() == "":
                        print("Password empty. Typing UID instead.")
                        print(uid_hex)
                        type_string(uid_hex)
                        green_led.value = True
                    else:
                        print("Password retrieved from sector 8:", password)
                        print(password)
                        type_string(password)
                        green_led.value = True

                    # Add a newline after typing
                    kbd.press(Keycode.ENTER)
                    kbd.release_all()
                    
                else:
                    print("Invalid data in sector 8.")
                    print(uid_hex)
                    type_string(uid_hex)
                    red_led.value = True
                    kbd.press(Keycode.ENTER)
                    kbd.release_all()
                    
                rfid.stop_crypto1()
            else:
                (stat, tag_type) = rfid.request(rfid.REQIDL)
                if stat == rfid.OK:
                    (stat, raw_uid) = rfid.SelectTagSN()

                    block_addr = 8
                    
                    if rfid.auth(rfid.AUTHENT1A, block_addr, default_key, raw_uid) == rfid.OK:
                        print("Authentication successful!")
                        
                        data = rfid.read(block_addr)
                        print(data)
                        
                        if status == rfid.OK and data is not None:
                            password = ''.join(chr(byte) for byte in data if byte != 0)
                            
                            if all(byte == 0 for byte in data):
                                print("Password empty. Typing UID instead.")
                                print(uid_hex)
                                type_string(uid_hex)
                                green_led.value = True
                                
                            elif password.strip() == "":
                                print("Password empty. Typing UID instead.")
                                print(uid_hex)
                                type_string(uid_hex)
                                green_led.value = True
                                
                            else:
                                print("Password retrieved from sector 8:", password)
                                print(password)
                                type_string(password)
                                green_led.value = True
                            
                            # Add a newline after typing
                            kbd.press(Keycode.ENTER)
                            kbd.release_all()
                            
                        else:
                            print("Invalid data in sector 8.")
                            print(uid_hex)
                            type_string(uid_hex)
                            red_led.value = True
                            kbd.press(Keycode.ENTER)
                            kbd.release_all()
                            
                    else:
                        print("Authentication failed. Typing UID instead.")
                        print(uid_hex)
                        type_string(uid_hex)
                        red_led.value = True
                        kbd.press(Keycode.ENTER)
                        kbd.release_all()
                        
                rfid.stop_crypto1()
                
        else:
            print("Failed to read card UID.")
            red_led.value = True

    time.sleep(0.2)
