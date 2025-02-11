import board
import digitalio
import time
from mfrc522 import MFRC522
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
import json
import random
import aesio

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

# Pad data to a multiple of 16 bytes for AES encryption
def pad_data(data):
    padding_length = 16 - (len(data) % 16)
    return data + bytes([padding_length] * padding_length)

# Remove padding from decrypted data
def unpad_data(data):
    padding_length = data[-1]
    return data[:-padding_length]

# Generate a 16-byte encryption key from the UID
def generate_encryption_key(raw_uid):
    # Pad the UID with zeros to make it 16 bytes
    return b'\x00' * (16 - len(raw_uid)) + bytes(raw_uid)

# Encrypt a single 16-byte block using AES ECB mode
def encrypt_block(block, key):
    cipher = aesio.AES(key, aesio.MODE_ECB)
    encrypted_block = bytearray(16)
    cipher.encrypt_into(block, encrypted_block)
    return encrypted_block

# Decrypt a single 16-byte block using AES ECB mode
def decrypt_block(block, key):
    cipher = aesio.AES(key, aesio.MODE_ECB)
    decrypted_block = bytearray(16)
    cipher.decrypt_into(block, decrypted_block)
    return decrypted_block

# Write password to the selected sector
def write_password_to_sector(password, sector, raw_uid):
    # Generate the encryption key from the UID
    encryption_key = generate_encryption_key(raw_uid)

    # Prepare the password data (encode to UTF-8 bytes)
    password_bytes = password.encode('utf-8')
    password_len = len(password_bytes)

    # Calculate CRC for the unencrypted password
    crc = calculate_crc(password_bytes)
    crc_bytes = [(crc >> 8) & 0xFF, crc & 0xFF]

    # Prepare the third block (CRC + password length)
    len_crc_block = crc_bytes + [password_len & 0xFF, (password_len >> 8) & 0xFF] + [0x00] * 12

    # Convert len_crc_block to bytes
    len_crc_block_bytes = bytes(len_crc_block)

    # Split the password into 16-byte blocks
    block1 = password_bytes[:16]
    block2 = password_bytes[16:32] if len(password_bytes) > 16 else []

    # Pad blocks to 16 bytes if necessary
    if len(block1) < 16:
        block1 = pad_data(block1)
    if block2 and len(block2) < 16:
        block2 = pad_data(block2)

    # Encrypt each block separately
    encrypted_block1 = encrypt_block(block1, encryption_key)
    encrypted_block2 = encrypt_block(block2, encryption_key) if block2 else b''
    encrypted_len_crc_block = encrypt_block(len_crc_block_bytes, encryption_key)

    # Show CRC to be stored
    print(f"CRC to be stored: {crc:04X}")

    # Authenticate and write to the sector
    if rfid.auth(rfid.AUTHENT1A, sector * 4, default_key, raw_uid) == rfid.OK:
        print(f"Authentication for sector {sector} successful!")

        # Write block 1 (first 16 bytes of encrypted password)
        if rfid.write(sector * 4, list(encrypted_block1)) == rfid.OK:
            print(f"Block 1 written to sector {sector}.")

            # Write block 2 (next 16 bytes of encrypted password, if any)
            if encrypted_block2:
                if rfid.write(sector * 4 + 1, list(encrypted_block2)) == rfid.OK:
                    print(f"Block 2 written to sector {sector}.")
                else:
                    print(f"Failed to write block 2 to sector {sector}.")
                    return False

            # Write block 3 (CRC + password length)
            if rfid.write(sector * 4 + 2, list(encrypted_len_crc_block)) == rfid.OK:
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
    # Generate the encryption key from the UID
    encryption_key = generate_encryption_key(raw_uid)

    # Read the password blocks back
    block1 = sector * 4
    block2 = sector * 4 + 1
    block3 = sector * 4 + 2

    if rfid.auth(rfid.AUTHENT1A, block1, default_key, raw_uid) == rfid.OK:
        # Read block 1 (first 16 bytes of encrypted password)
        data1 = rfid.read(block1)
        if data1 is None:
            print(f"Failed to read block 1 from sector {sector}.")
            return False

        # Read block 2 (next 16 bytes of encrypted password, if any)
        data2 = rfid.read(block2)
        if data2 is None:
            print(f"Failed to read block 2 from sector {sector}.")
            return False

        # Read block 3 (CRC + password length)
        data3 = rfid.read(block3)
        if data3 is None:
            print(f"Failed to read block 3 from sector {sector}.")
            return False

        # Decrypt each block separately
        decrypted_block1 = decrypt_block(bytes(data1), encryption_key)
        decrypted_block2 = decrypt_block(bytes(data2), encryption_key) if data2 else b''
        decrypted_len_crc_block = decrypt_block(bytes(data3), encryption_key)

        # Extract CRC and password length from decrypted block 3
        stored_crc = (decrypted_len_crc_block[0] << 8) | decrypted_len_crc_block[1]  # First two bytes: CRC
        password_len = (decrypted_len_crc_block[2] << 8) | decrypted_len_crc_block[3]  # Next two bytes: password length

        # Combine decrypted blocks and trim to actual password length
        decrypted_password_bytes = decrypted_block1 + decrypted_block2
        decrypted_password_bytes = decrypted_password_bytes[:password_len]

        # Calculate CRC for the decrypted password
        calculated_crc = calculate_crc(decrypted_password_bytes)

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
