import board
import digitalio
import time
from mfrc522 import MFRC522
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
import json
import aesio
import asyncio

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

# Initialize button (connected to GPIO 15 and GND)
button = digitalio.DigitalInOut(board.GP15)
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.UP  # Enable internal pull-up resistor

# Variables to track button state and timing
button_was_pressed = False
last_press_time = 0
press_count = 0
click_time_frame = 1  # 1-second frame to count clicks

# Slot selection
current_slot = 1

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

# Generate a 16-byte encryption key from the UID
def generate_encryption_key(raw_uid):
    # Pad the UID with zeros to make it 16 bytes
    return b'\x00' * (16 - len(raw_uid)) + bytes(raw_uid)

# Decrypt a single 16-byte block using AES ECB mode
def decrypt_block(block, key):
    cipher = aesio.AES(key, aesio.MODE_ECB)
    decrypted_block = bytearray(16)
    cipher.decrypt_into(block, decrypted_block)
    return decrypted_block

# Function to read and decrypt password from a specific slot
def read_password_from_slot(slot, raw_uid):
    sector = slot  # Slot 1 = Sector 1, Slot 2 = Sector 2, ..., Slot 15 = Sector 15
    block1 = sector * 4  # First block of the sector
    block2 = sector * 4 + 1  # Second block of the sector
    block3 = sector * 4 + 2  # Third block of the sector (length + CRC)

    # Generate the encryption key from the UID
    encryption_key = generate_encryption_key(raw_uid)

    # Authenticate with the default key for the sector
    if rfid.auth(rfid.AUTHENT1A, block1, default_key, raw_uid) == rfid.OK:
        print(f"Authentication for sector {sector} successful!")

        # Read block 1 (first 16 bytes of encrypted password)
        data1 = rfid.read(block1)
        if data1 is None:
            print(f"Failed to read block 1 from sector {sector}.")
            return None

        # Read block 2 (next 16 bytes of encrypted password, if any)
        data2 = rfid.read(block2)
        if data2 is None:
            print(f"Failed to read block 2 from sector {sector}.")
            return None

        # Read block 3 (encrypted CRC + password length)
        data3 = rfid.read(block3)
        if data3 is None:
            print(f"Failed to read block 3 from sector {sector}.")
            return None

        # Decrypt each block separately
        decrypted_block1 = decrypt_block(bytes(data1), encryption_key)
        decrypted_block2 = decrypt_block(bytes(data2), encryption_key) if data2 else b''
        decrypted_block3 = decrypt_block(bytes(data3), encryption_key)

        # Extract CRC and password length from decrypted block 3
        stored_crc = (decrypted_block3[0] << 8) | decrypted_block3[1]  # First two bytes: CRC
        password_len = (decrypted_block3[2] << 8) | decrypted_block3[3]  # Next two bytes: password length

        # Combine decrypted password blocks and trim to actual password length
        decrypted_password_bytes = decrypted_block1 + decrypted_block2
        decrypted_password_bytes = decrypted_password_bytes[:password_len]

        # Calculate CRC for the decrypted password
        calculated_crc = calculate_crc(decrypted_password_bytes)

        # Debugging: Print the stored and calculated CRC
        print(f"Stored CRC: {stored_crc:04X}")
        print(f"Calculated CRC: {calculated_crc:04X}")

        # Verify CRC
        if stored_crc == calculated_crc:
            # Decode the password from UTF-8 bytes
            password = decrypted_password_bytes.decode('utf-8')
            print(f"Password retrieved from slot {slot} (sector {sector}): {password}")
            return password
        else:
            print(f"CRC verification failed for slot {slot} (sector {sector}). Data may be corrupted.")
            return None
    else:
        print(f"Authentication for sector {sector} failed.")
        return None

# Card presence tracking
card_present = False  # Flag to track if a card is currently on the sensor
last_card_uid = None  # Store the last detected card UID
debounce_time = 5.0  # Debounce delay in seconds
last_detection_time = 0  # Timestamp of the last card detection

async def handle_button():
    global button_was_pressed, press_count, last_press_time, current_slot

    while True:
        # Check if the button is pressed (button.value is False when pressed)
        if not button.value:
            if not button_was_pressed:
                # Button was just pressed
                button_was_pressed = True
                press_count += 1
                last_press_time = time.monotonic()
                print(f"Button pressed! Press count: {press_count}")  # Debugging
        else:
            if button_was_pressed:
                # Button was just released
                button_was_pressed = False
                print("Button released!")  # Debugging

        # Check if the time frame for counting clicks has passed
        if time.monotonic() - last_press_time > click_time_frame and press_count > 0:
            # Evaluate the number of clicks within the time frame
            if press_count == 1:
                # Single click: increment slot number
                current_slot = (current_slot % 15) + 1
                print(f"Single click detected. Current slot: {current_slot}")
                await blink_green_led(current_slot)

    # Reset the press count after evaluating
    press_count = 0

        await asyncio.sleep(0.05)

async def blink_green_led(times):
    """Blink the green LED a specific number of times."""
    for _ in range(times):
        green_led.value = True
        await asyncio.sleep(0.2)
        green_led.value = False
        await asyncio.sleep(0.2)

async def main():
    # Run all tasks concurrently
    await asyncio.gather(
        handle_button(),
        rfid_loop()
    )

async def rfid_loop():
    global card_present, last_card_uid, last_detection_time, current_slot

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

                    # Read and decrypt password from the current slot
                    password = read_password_from_slot(current_slot, raw_uid)
                    if password:
                        print("Password retrieved:", password)
                        type_string(password)
                        green_led.value = True
                    else:
                        print("Failed to read password from slot.", current_slot)
                        red_led.value = True

                    # Add a newline after typing
                    kbd.press(Keycode.ENTER)
                    kbd.release_all()

                    rfid.stop_crypto1()

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

        await asyncio.sleep(0.1)  # Small delay to reduce CPU usage

# Run the asyncio event loop
asyncio.run(main())
