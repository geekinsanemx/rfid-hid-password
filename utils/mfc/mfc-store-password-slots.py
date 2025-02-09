import board
import digitalio
import time
from mfrc522 import MFRC522
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
import json
import random

# Manually define printable ASCII characters
ascii_letters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
digits = '0123456789'
punctuation = '~!@#$%^&*()-_+={}[]|\;:<>,./?'
printable = ascii_letters + digits + punctuation

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

# Function to generate a random 32-byte password
def generate_random_password():
    return ''.join(random.choice(printable) for _ in range(32))

# Load default key from JSON file
def load_default_key(file_path):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            return data.get('default_key', [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF])
    except Exception as e:
        print(f"Error loading default key: {e}. Using default key.")
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

# Prepare password for storage
def prepare_password(password):
    # Encode the password to UTF-8 bytes
    password_bytes = password.encode('utf-8')
    password_len = len(password_bytes)

    # Split password into blocks of 16 bytes
    block1 = password_bytes[:16]
    block2 = password_bytes[16:32] if password_len > 16 else []

    # Pad blocks to 16 bytes if necessary
    if len(block1) < 16:
        block1 = block1.ljust(16, b'\x00')
    if block2 and len(block2) < 16:
        block2 = block2.ljust(16, b'\x00')

    return block1, block2, password_len

# Check if a sector is empty (skip trailer block)
def is_sector_empty(sector, raw_uid):
    if rfid.auth(rfid.AUTHENT1A, sector * 4, default_key, raw_uid) == rfid.OK:
        # Check only the first three blocks (ignore the trailer block)
        for block in range(3):  # Blocks 0, 1, and 2
            data = rfid.read(sector * 4 + block)
            if data is not None and any(byte != 0 for byte in data):
                return False
        return True
    return False

# Prompt user to select a sector
def select_sector(raw_uid):
    print("Available sectors (slots):")
    available_sectors = []
    for sector in range(1, 16):  # Sectors 1 to 15
        if is_sector_empty(sector, raw_uid):
            available_sectors.append(sector)
            print(f"  Slot {sector} (Sector {sector})")

    if not available_sectors:
        print("No available sectors. All sectors are in use.")
        return None

    while True:
        try:
            selected_sector = int(input("Select a sector (slot) to store the password: "))
            if selected_sector in available_sectors:
                return selected_sector
            else:
                print("Invalid selection. Please choose an available sector.")
        except ValueError:
            print("Invalid input. Please enter a number.")

# Write password to the selected sector
def write_password_to_sector(password, sector, raw_uid):
    # Prepare password data
    block1, block2, password_len = prepare_password(password)

    # Calculate CRC for the password
    password_bytes = block1 + block2 if block2 else block1
    crc = calculate_crc(password_bytes)
    crc_bytes = [(crc >> 8) & 0xFF, crc & 0xFF]

    # Prepare third block (CRC + password length)
    len_crc_block = crc_bytes + [password_len & 0xFF, (password_len >> 8) & 0xFF] + [0x00] * 12

    # Show CRC to be stored
    print(f"CRC to be stored: {crc:04X}")

    # Authenticate and write to the sector
    if rfid.auth(rfid.AUTHENT1A, sector * 4, default_key, raw_uid) == rfid.OK:
        print(f"Authentication for sector {sector} successful!")

        # Write block 1 (first 16 bytes of password)
        if rfid.write(sector * 4, list(block1)) == rfid.OK:
            print(f"Block 1 written to sector {sector}.")

            # Write block 2 (next 16 bytes of password, if any)
            if block2:
                if rfid.write(sector * 4 + 1, list(block2)) == rfid.OK:
                    print(f"Block 2 written to sector {sector}.")
                else:
                    print(f"Failed to write block 2 to sector {sector}.")
                    return False

            # Write block 3 (CRC + password length)
            if rfid.write(sector * 4 + 2, len_crc_block) == rfid.OK:
                print(f"Block 3 (CRC + length) written to sector {sector}.")
                return True
            else:
                print(f"Failed to write block 3 to sector {sector}.")
                return False
        else:
            print(f"Failed to write block 1 to sector {sector}.")
            return False
    else:
        print(f"Authentication for sector {sector} failed.")
        return False

# Function to validate the stored password
def validate_stored_password(sector, raw_uid):
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

# Main logic
def manage_password():
    print("Waiting for RFID/NFC card...")
    rfid.init()

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

            # Prompt user to select a sector
            selected_sector = select_sector(raw_uid)
            if selected_sector is None:
                print("No available sectors. Exiting.")
                return

            # Ask if user wants to use a random password
            use_random = input("Do you want to use a random 32-byte password? (yes/no): ").strip().lower()
            if use_random == 'yes':
                password_to_store = generate_random_password()
                print(f"Generated password: {password_to_store}")
            else:
                password_to_store = input("Enter your password (max 32 bytes): ").strip()
                if len(password_to_store.encode('utf-8')) > 32:
                    print("Password is too long. Maximum length is 32 bytes.")
                    red_led.value = True
                    return

            # Write password to the selected sector
            if write_password_to_sector(password_to_store, selected_sector, raw_uid):
                print("Password successfully written!")

                # Validate the stored password
                if validate_stored_password(selected_sector, raw_uid):
                    print("Password validation successful! Data is intact.")
                    green_led.value = True
                else:
                    print("Password validation failed. Data may be corrupted.")
                    red_led.value = True
            else:
                print("Failed to write password.")
                red_led.value = True

            rfid.stop_crypto1()
        else:
            print("Failed to read card UID.")
            red_led.value = True
    else:
        print("No card detected.")
        red_led.value = True

    time.sleep(1)
    red_led.value = False
    green_led.value = False
    blue_led.value = False

# Example usage
manage_password()