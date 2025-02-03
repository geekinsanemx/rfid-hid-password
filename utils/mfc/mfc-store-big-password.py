import board
import digitalio
import time
from mfrc522 import MFRC522
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
import json
import binascii  # For CRC32 checksum

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

# Turn off LEDs initially
red_led.value = False
green_led.value = False

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

# Function to calculate CRC32 checksum
def calculate_checksum(data):
    return binascii.crc32(data.encode('utf-8')) & 0xFFFFFFFF

# Function to write a large string to the smartcard
def write_large_string(rfid, start_block, large_string, key):
    chunk_size = 16
    chunks = [large_string[i:i + chunk_size] for i in range(0, len(large_string), chunk_size)]
    checksum = calculate_checksum(large_string)

    for i, chunk in enumerate(chunks):
        block_addr = start_block + i

        # Check if the block is a sector trailer (e.g., block 3, 7, 11, etc.)
        if (block_addr + 1) % 4 == 0:
            print(f"Skipping sector trailer block {block_addr} to protect access bits.")
            continue

        # Authenticate before writing
        if rfid.auth(rfid.AUTHENT1A, block_addr, key, rfid.get_uid()):
            # Pad the chunk with null bytes to make it 16 bytes long
            padded_chunk = chunk.ljust(chunk_size, '\x00')
            data = padded_chunk.encode('utf-8')

            # Write the data to the block
            if rfid.write(block_addr, data):
                print(f"Block {block_addr} written successfully.")
            else:
                print(f"Failed to write to block {block_addr}.")
        else:
            print(f"Authentication failed for block {block_addr}.")

    # Write the checksum to the last block
    checksum_block = start_block + len(chunks)
    if rfid.auth(rfid.AUTHENT1A, checksum_block, key, rfid.get_uid()):
        checksum_data = checksum.to_bytes(4, byteorder='big').ljust(16, b'\x00')
        if rfid.write(checksum_block, checksum_data):
            print(f"Checksum written to block {checksum_block}.")
        else:
            print(f"Failed to write checksum to block {checksum_block}.")

# Function to read a large string from the smartcard
def read_large_string(rfid, start_block, num_blocks, key):
    large_string = ""
    for i in range(num_blocks):
        block_addr = start_block + i

        # Check if the block is a sector trailer (e.g., block 3, 7, 11, etc.)
        if (block_addr + 1) % 4 == 0:
            print(f"Skipping sector trailer block {block_addr}.")
            continue

        # Authenticate before reading
        if rfid.auth(rfid.AUTHENT1A, block_addr, key, rfid.get_uid()):
            data = rfid.read(block_addr)
            if data:
                # Decode the data and remove padding (null bytes)
                chunk = data.decode('utf-8').rstrip('\x00')
                large_string += chunk
            else:
                print(f"Failed to read block {block_addr}.")
                break
        else:
            print(f"Authentication failed for block {block_addr}.")
            break

    # Read the checksum from the last block
    checksum_block = start_block + num_blocks
    if rfid.auth(rfid.AUTHENT1A, checksum_block, key, rfid.get_uid()):
        checksum_data = rfid.read(checksum_block)
        if checksum_data:
            stored_checksum = int.from_bytes(checksum_data[:4], byteorder='big')
            calculated_checksum = calculate_checksum(large_string)
            if stored_checksum == calculated_checksum:
                print("Data integrity verified.")
            else:
                print("Data integrity check failed. Data may be corrupted.")
        else:
            print("Failed to read checksum.")
    else:
        print("Authentication failed for checksum block.")

    return large_string

# Main loop
print("Waiting for RFID/NFC card...")
while True:
    # Turn off LEDs at the start of each loop
    red_led.value = False
    green_led.value = False

    # Scan for cards
    (status, tag_type) = rfid.request(rfid.REQIDL)
    if status == rfid.OK:
        print("Card detected!")
        (status, raw_uid) = rfid.SelectTagSN()

        if status == rfid.OK:
            uid_hex = ''.join('{:02X}'.format(x) for x in raw_uid)
            print("Card UID:", uid_hex)

            # Example: Write a large string to the card
            large_string = "5PrHe46RVKcvtRqI9y#ZeJIOKGmS5&JHF%M#uSwXWcV1K2Lq"
            start_block = 8  # Starting block address
            num_blocks = (len(large_string) // 16) + 1  # Number of blocks needed

            # Write the large string
            write_large_string(rfid, start_block, large_string, default_key)

            # Read the large string
            retrieved_string = read_large_string(rfid, start_block, num_blocks, default_key)
            print("Retrieved string:", retrieved_string)

            # Indicate success with green LED
            green_led.value = True
        else:
            print("Failed to read card UID.")
            red_led.value = True

    time.sleep(10)