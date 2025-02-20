import board
import digitalio
import time
from mfrc522 import MFRC522
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
import json
import binascii

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
red_led = digitalio.DigitalInOut(board.GP27)
red_led.direction = digitalio.Direction.OUTPUT
green_led = digitalio.DigitalInOut(board.GP28)
green_led.direction = digitalio.Direction.OUTPUT
blue_led = digitalio.DigitalInOut(board.GP29)
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

# Global variable to select the default sector/slot
DEFAULT_SECTOR = 1  # Default to sector 1

# Card presence tracking
card_present = False  # Flag to track if a card is currently on the sensor
last_card_uid = None  # Store the last detected card UID
debounce_time = 10.0  # Debounce delay in seconds
last_detection_time = 0  # Timestamp of the last card detection

# CRC-16 checksum calculation
def calculate_crc(data):
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF
    return crc

def read_password_from_sector(sector):
    """Read password from the specified sector."""
    block_addr = sector * 4  # Each sector has 4 blocks
    password_blocks = [block_addr, block_addr + 1]
    crc_block = block_addr + 2

    password_data = []
    for block in password_blocks:
        data = rfid.read(block)
        if data is not None:
            password_data.extend(data)

    crc_data = rfid.read(crc_block)
    if crc_data is not None:
        stored_crc = (crc_data[0] << 8) | crc_data[1]  # First two bytes: CRC
        password_len = (crc_data[2] << 8) | crc_data[3]  # Next two bytes: password length

        # Verify CRC
        calculated_crc = calculate_crc(bytes(password_data[:password_len]))
        if calculated_crc == stored_crc:
            return ''.join(chr(byte) for byte in password_data[:password_len])
        else:
            print("CRC mismatch. Password may be corrupted.")
            return None
    else:
        print("Failed to read CRC block.")
        return None

def validate_stored_password(sector, raw_uid):
    """Validate the stored password using its CRC."""
    # Read the password blocks back
    block1 = sector * 4
    block2 = sector * 4 + 1
    block3 = sector * 4 + 2

    if rfid.auth(rfid.AUTHENT1A, block1, default_key, raw_uid) == rfid.OK:
        # Read block 1 (first 16 bytes of password)
        data1 = rfid.read(block1)
        if data1 is None:
            print(f"Failed to read block 1 from sector {sector}.")
            return False

        # Read block 2 (next 16 bytes of password, if any)
        data2 = rfid.read(block2)
        if data2 is None:
            print(f"Failed to read block 2 from sector {sector}.")
            return False

        # Read block 3 (CRC + password length)
        data3 = rfid.read(block3)
        if data3 is None:
            print(f"Failed to read block 3 from sector {sector}.")
            return False

        # Extract CRC and password length from block 3
        stored_crc = (data3[0] << 8) | data3[1]  # First two bytes: CRC
        password_len = (data3[2] << 8) | data3[3]  # Next two bytes: password length

        # Combine password data from block 1 and block 2
        password_bytes = bytes(data1) + bytes(data2)
        password_bytes = password_bytes[:password_len]  # Trim to actual password length

        # Calculate CRC for the password
        calculated_crc = calculate_crc(password_bytes)

        # Verify CRC
        if stored_crc == calculated_crc:
            print(f"Password validation successful! CRC matched: {stored_crc:04X}")
            return True
        else:
            print(f"Password validation failed. Data may be corrupted.")
            print(f"Stored CRC: {stored_crc:04X}")
            print(f"Calculated CRC: {calculated_crc:04X}")
            return False
    else:
        print(f"Authentication for sector {sector} failed.")
        return False

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
        # Get the UID of the card
        (status, raw_uid) = rfid.SelectTagSN()

        if status == rfid.OK:
            uid_hex = ''.join('{:02X}'.format(x) for x in raw_uid)

            # Check if the card is new or the same as the last one
            if uid_hex != last_card_uid or (time.monotonic() - last_detection_time) > debounce_time:
                print("Card detected!")
                card_present = True
                last_card_uid = uid_hex
                last_detection_time = time.monotonic()

                print("Card UID:", uid_hex)
                print("  - tag type: 0x%02x" % tag_type)

                if rfid.auth(rfid.AUTHENT1A, DEFAULT_SECTOR * 4, default_key, raw_uid) == rfid.OK:
                    print("Authentication successful!")

                    password = read_password_from_sector(DEFAULT_SECTOR)
                    if password:
                        print("Password retrieved from sector", DEFAULT_SECTOR, ":", password)

                        # Validate the password using its CRC
                        if validate_stored_password(DEFAULT_SECTOR, raw_uid):
                            print("Password is valid. Typing password...")
                            type_string(password)
                            green_led.value = True
                        else:
                            print("Password validation failed. Typing UID instead.")
                            type_string(uid_hex)
                            blue_led.value = True
                    else:
                        print("Failed to read password. Typing UID instead.")
                        type_string(uid_hex)
                        blue_led.value = True

                else:
                    print("Authentication failed. Typing UID instead.")
                    type_string(uid_hex)
                    blue_led.value = True

                # Add a newline after typing
                kbd.press(Keycode.ENTER)
                kbd.release_all()

                rfid.stop_crypto1()
                time.sleep(1)

            else:
                # Card is still present, but we've already processed it
                pass

        else:
            print("Failed to read card UID.")
            red_led.value = True

    else:
        if card_present and (time.monotonic() - last_detection_time) > debounce_time:
            # Card is no longer detected
            print("Card removed.")
            card_present = False
            last_card_uid = None

    time.sleep(0.1)  # Small delay to reduce CPU usage
