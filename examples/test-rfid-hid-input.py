import board
import busio
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

# Default key for authentication
default_key = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]

# Mapping of digits to Keycode values
digit_to_keycode = {
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
}

# Mapping of letters to Keycode values
letter_to_keycode = {
    'A': Keycode.A,
    'B': Keycode.B,
    'C': Keycode.C,
    'D': Keycode.D,
    'E': Keycode.E,
    'F': Keycode.F,
}

def dump_smartcard(rfid, uid, key):
    """Dump the content of all sectors of the smartcard."""
    print("Dumping smartcard content:")
    for sector in range(16):  # Assuming a 1K card with 16 sectors
        for block in range(4):  # Each sector has 4 blocks
            block_addr = sector * 4 + block
            if block % 4 == 3:
                # Skip sector trailer blocks (block 3 in each sector)
                print(f"Sector {sector}, Block {block}: Skipping sector trailer")
                continue

            if rfid.auth(rfid.AUTHENT1A, block_addr, key, uid) == rfid.OK:
                (status, data) = rfid.read(block_addr)
                if status == rfid.OK:
                    print(f"Sector {sector}, Block {block}: {data}")
                else:
                    print(f"Sector {sector}, Block {block}: Failed to read (status: {status})")
            else:
                print(f"Sector {sector}, Block {block}: Authentication failed")
        print()  # Add a newline between sectors

# Main loop
print("Waiting for RFID/NFC card...")
while True:
    # Scan for cards
    (status, tag_type) = rfid.request(rfid.REQIDL)
    if status == rfid.OK:
        print("Card detected!")

        # Get the UID of the card
        (status, raw_uid) = rfid.anticoll()
        if status == rfid.OK:
            uid_hex = ''.join('{:02X}'.format(x) for x in raw_uid)
            print("Card UID:", uid_hex)

            # Dump the content of all sectors
            dump_smartcard(rfid, raw_uid, default_key)

            # Type the UID as a simulated keyboard input
            for char in uid_hex:
                if char.isdigit():
                    # Map digits to Keycode.ZERO to Keycode.NINE
                    keycode = digit_to_keycode.get(char, None)
                else:
                    # Map letters to Keycode.A to Keycode.F
                    keycode = letter_to_keycode.get(char.upper(), None)

                if keycode is not None:
                    kbd.press(keycode)
                    kbd.release_all()

            # Add a newline after typing the UID
            kbd.press(Keycode.ENTER)
            kbd.release_all()

        time.sleep(1)  # Delay to avoid multiple reads
