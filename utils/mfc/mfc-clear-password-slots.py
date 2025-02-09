import board
import digitalio
import time
from mfrc522 import MFRC522
import json

# Define SPI pins for RP2040-Zero
sck = board.GP2
mosi = board.GP3
miso = board.GP4
cs = board.GP0
rst = board.GP1

# Initialize MFRC522
rfid = MFRC522(sck, mosi, miso, rst, cs)

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

# Default trailer block (key A, access bits, key B)
default_trailer_block = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x07, 0x80, 0x69, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]

def is_sector_in_use(sector, raw_uid):
    """Check if a sector is in use (contains data in blocks 0, 1, or 2)."""
    if rfid.auth(rfid.AUTHENT1A, sector * 4, default_key, raw_uid) == rfid.OK:
        for block in range(3):  # Blocks 0, 1, and 2
            data = rfid.read(sector * 4 + block)
            if data is not None and any(byte != 0 for byte in data):
                return True
        return False
    else:
        print(f"Authentication for sector {sector} failed.")
        return False

def read_sector_data(sector, raw_uid):
    """Read data from a specific sector and decode the password and CRC."""
    if rfid.auth(rfid.AUTHENT1A, sector * 4, default_key, raw_uid) == rfid.OK:
        print(f"Authentication for sector {sector} successful!")

        # Read block 0 and block 1 (password data)
        block0 = rfid.read(sector * 4)
        block1 = rfid.read(sector * 4 + 1)
        if block0 is None or block1 is None:
            print(f"Failed to read password data from sector {sector}.")
            return None

        # Read block 2 (password length and CRC)
        block2 = rfid.read(sector * 4 + 2)
        if block2 is None:
            print(f"Failed to read CRC data from sector {sector}.")
            return None

        # Extract password length and CRC (little-endian format)
        password_len = (block2[1] << 8) | block2[0]  # First two bytes: password length
        stored_crc = (block2[3] << 8) | block2[2]  # Next two bytes: CRC (little-endian)

        # Combine password data from block 0 and block 1
        password_bytes = bytes(block0) + bytes(block1)
        password_bytes = password_bytes[:password_len]  # Trim to actual password length

        # Decode the password from UTF-8 bytes
        password = password_bytes.decode('utf-8')

        return password, stored_crc
    else:
        print(f"Authentication for sector {sector} failed.")
        return None

def clear_sector(sector, raw_uid):
    """Clear all data blocks and reset the trailer block for a specific sector."""
    if rfid.auth(rfid.AUTHENT1A, sector * 4, default_key, raw_uid) == rfid.OK:
        print(f"Authentication for sector {sector} successful!")

        # Clear data blocks (blocks 0, 1, and 2)
        for block in range(3):  # Blocks 0, 1, and 2
            write_status = rfid.write(sector * 4 + block, [0x00] * 16)  # Write 16 zeros
            if write_status == rfid.OK:
                print(f"Block {block} cleared successfully!")
            else:
                print(f"Failed to clear block {block}.")
                return False

        # Reset the trailer block (block 3) to default values
        write_status = rfid.write(sector * 4 + 3, default_trailer_block)
        if write_status == rfid.OK:
            print(f"Trailer block reset to default values.")
            return True
        else:
            print(f"Failed to reset trailer block.")
            return False
    else:
        print(f"Authentication for sector {sector} failed.")
        return False

def clear_sectors():
    # Main loop
    print("Waiting for RFID/NFC card to clear sectors...")

    # Turn off LEDs at the start of each loop
    red_led.value = False
    green_led.value = False
    blue_led.value = False

    # Scan for cards
    rfid.init()
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

            # Check which sectors are in use
            in_use_sectors = []
            for sector in range(1, 16):  # Sectors 1 to 15
                if is_sector_in_use(sector, raw_uid):
                    in_use_sectors.append(sector)

            if not in_use_sectors:
                print("No sectors in use. All sectors are empty.")
                return

            # Display list of sectors in use
            print("Sectors in use (can be cleared):")
            for sector in in_use_sectors:
                print(f"  Slot {sector} (Sector {sector})")
            print("  Option: all")

            # Prompt user to select a slot to clear
            user_input = input("Enter the slot number to clear (1-15) or 'all' to clear all sectors: ").strip().lower()

            if user_input == "all":
                # Clear all sectors
                for sector in range(1, 16):
                    if sector in in_use_sectors:
                        print(f"Clearing sector {sector}...")
                        if clear_sector(sector, raw_uid):
                            print(f"Sector {sector} cleared successfully!")
                            green_led.value = True
                        else:
                            print(f"Failed to clear sector {sector}.")
                            red_led.value = True
                    else:
                        print(f"Sector {sector} is empty or invalid. Skipping...")
                return
            else:
                try:
                    slot = int(user_input)
                    if slot < 1 or slot > 15:
                        print("Invalid slot number. Please enter a number between 1 and 15.")
                        return
                    if slot not in in_use_sectors:
                        print("Selected slot is empty or invalid. Please choose a sector from the list above.")
                        return

                    # Read and display data from the selected sector
                    sector_data = read_sector_data(slot, raw_uid)
                    if sector_data:
                        password, stored_crc = sector_data
                        print(f"Stored Password: {password}")
                        print(f"Stored CRC: {stored_crc:04X}")

                        # Ask for confirmation before clearing
                        confirmation = input("Are you sure you want to clear this sector? (yes/no): ").strip().lower()
                        if confirmation == "yes":
                            # Clear the sector
                            if clear_sector(slot, raw_uid):
                                print(f"Sector {slot} cleared successfully!")
                                green_led.value = True
                            else:
                                print(f"Failed to clear sector {slot}.")
                                red_led.value = True
                        else:
                            print("Clear operation cancelled.")
                    else:
                        print(f"No valid data found in slot {slot} (sector {slot}).")

                except ValueError:
                    print("Invalid input. Please enter a number or 'all'.")
                    return

            rfid.stop_crypto1()

        else:
            print("Failed to read card UID.")
            red_led.value = True

# Run the clear sectors function
clear_sectors()
time.sleep(1)
red_led.value = False
green_led.value = False
blue_led.value = False
