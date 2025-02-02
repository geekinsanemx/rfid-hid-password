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

# Global variables for password and CRC sectors
passwd_sector = 8  # Sector to store the password
passwd_crc_sector = 9  # Sector to store the CRC checksum

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

# Ensure the password is exactly 16 bytes when encoded in UTF-8
def prepare_password(password):
    # Encode the password to UTF-8 bytes
    password_bytes = password.encode('utf-8')
    
    # If the password is longer than 16 bytes, truncate it
    print(f"password_size {len(password_bytes)}")
    if len(password_bytes) > 16:
        password_bytes = password_bytes[:16]
    # If the password is shorter than 16 bytes, pad it with null bytes
    elif len(password_bytes) < 16:
        password_bytes = password_bytes.ljust(16, b'\x00')
    
    return password_bytes

def read_password_with_crc():
    # Main loop
    print("Waiting for RFID/NFC card to read password...")

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

            # Check if the card is an NTAG
            if rfid.IsNTAG():
                print("Detected NTAG card. Skipping authentication.")

                # Read password from the password sector
                sector_data = rfid.read(passwd_sector)
                if sector_data is not None:
                    # Read CRC from the CRC sector
                    crc_data = rfid.read(passwd_crc_sector)
                    if crc_data is not None:
                        # Extract CRC from the CRC sector
                        stored_crc = (crc_data[0] << 8) | crc_data[1]

                        # Calculate CRC for the password
                        calculated_crc = calculate_crc(sector_data)

                        # Verify CRC
                        if stored_crc == calculated_crc:
                            # Decode the password from UTF-8 bytes, removing padding
                            password = bytes(sector_data).decode('utf-8').rstrip('\x00')
                            print(f"Password retrieved from sector {passwd_sector}:", password)
                            print("CRC verification successful!")
                            green_led.value = True
                            return password  # Return the password if it exists and CRC matches
                        else:
                            print("CRC verification failed. Data may be corrupted.")
                            red_led.value = True
                    else:
                        print(f"Failed to read CRC from sector {passwd_crc_sector}.")
                        red_led.value = True
                else:
                    print(f"Failed to read password from sector {passwd_sector}.")
                    red_led.value = True

            else:
                print("Detected non-NTAG card. Authenticating...")
                (stat, tag_type) = rfid.request(rfid.REQIDL)
                if stat == rfid.OK:
                    (stat, raw_uid) = rfid.SelectTagSN()

                    # Authenticate with the default key for the password sector
                    if rfid.auth(rfid.AUTHENT1A, passwd_sector, default_key, raw_uid) == rfid.OK:
                        print(f"Authentication for sector {passwd_sector} successful!")

                        # Read password from the password sector
                        sector_data = rfid.read(passwd_sector)
                        if sector_data is not None:
                            # Authenticate with the default key for the CRC sector
                            if rfid.auth(rfid.AUTHENT1A, passwd_crc_sector, default_key, raw_uid) == rfid.OK:
                                print(f"Authentication for sector {passwd_crc_sector} successful!")

                                # Read CRC from the CRC sector
                                crc_data = rfid.read(passwd_crc_sector)
                                if crc_data is not None:
                                    # Extract CRC from the CRC sector
                                    stored_crc = (crc_data[0] << 8) | crc_data[1]

                                    # Calculate CRC for the password
                                    calculated_crc = calculate_crc(sector_data)

                                    # Verify CRC
                                    if stored_crc == calculated_crc:
                                        # Decode the password from UTF-8 bytes, removing padding
                                        password = bytes(sector_data).decode('utf-8').rstrip('\x00')
                                        print(f"Password retrieved from sector {passwd_sector}:", password)
                                        print("CRC verification successful!")
                                        green_led.value = True
                                        return password  # Return the password if it exists and CRC matches
                                    else:
                                        print("CRC verification failed. Data may be corrupted.")
                                        red_led.value = True
                                else:
                                    print(f"Failed to read CRC from sector {passwd_crc_sector}.")
                                    red_led.value = True
                            else:
                                print(f"Authentication for sector {passwd_crc_sector} failed.")
                                red_led.value = True
                        else:
                            print(f"Failed to read password from sector {passwd_sector}.")
                            red_led.value = True
                    else:
                        print(f"Authentication for sector {passwd_sector} failed.")
                        red_led.value = True

            rfid.stop_crypto1()

        else:
            print("Failed to read card UID.")
            red_led.value = True


def write_password_with_crc(password):
    # Convert password to UTF-8 encoded bytes
    password_bytes = prepare_password(password)

    # Calculate CRC-16 checksum for the password
    crc = calculate_crc(password_bytes)
    crc_bytes = [(crc >> 8) & 0xFF, crc & 0xFF]

    # Print the password in text and bytes format
    print("Password to write (text):", password)
    print("Password to write (bytes):", password_bytes)

    # Wait for user confirmation
    confirmation = input("Confirm writing the password? (yes/no): ").strip().lower()
    if confirmation != 'yes':
        print("Password writing cancelled.")
        return False

    # Main loop
    print("Waiting for RFID/NFC card to write password and CRC...")
    
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

            # Check if the card is an NTAG
            if rfid.IsNTAG():
                print("Detected NTAG card. Skipping authentication.")

                # Check if the password sector is empty
                sector_data = rfid.read(passwd_sector)
                if sector_data is not None and all(byte == 0 for byte in sector_data):
                    print(f"Sector {passwd_sector} is empty. Writing password...")

                    # Write the password to the password sector
                    write_status = rfid.write(passwd_sector, list(password_bytes))
                    if write_status == rfid.OK:
                        print(f"Password successfully written to sector {passwd_sector}!")

                        # Write the CRC to the CRC sector
                        write_status = rfid.write(passwd_crc_sector, crc_bytes + [0x00] * 14)  # Pad to 16 bytes
                        if write_status == rfid.OK:
                            print(f"CRC successfully written to sector {passwd_crc_sector}!")
                            green_led.value = True
                            return True  # Return True if write is successful
                        else:
                            print(f"Failed to write CRC to sector {passwd_crc_sector}.")
                            red_led.value = True
                    else:
                        print(f"Failed to write password to sector {passwd_sector}.")
                        red_led.value = True
                else:
                    print(f"Sector {passwd_sector} is not empty. Cannot write password.")
                    red_led.value = True

            else:
                print("Detected non-NTAG card. Authenticating...")
                (stat, tag_type) = rfid.request(rfid.REQIDL)
                if stat == rfid.OK:
                    (stat, raw_uid) = rfid.SelectTagSN()

                    # Authenticate with the default key for the password sector
                    if rfid.auth(rfid.AUTHENT1A, passwd_sector, default_key, raw_uid) == rfid.OK:
                        print(f"Authentication for sector {passwd_sector} successful!")

                        # Check if the password sector is empty
                        sector_data = rfid.read(passwd_sector)
                        if sector_data is not None and all(byte == 0 for byte in sector_data):
                            print(f"Sector {passwd_sector} is empty. Writing password...")

                            # Write the password to the password sector
                            write_status = rfid.write(passwd_sector, list(password_bytes))
                            if write_status == rfid.OK:
                                print(f"Password successfully written to sector {passwd_sector}!")

                                # Authenticate with the default key for the CRC sector
                                if rfid.auth(rfid.AUTHENT1A, passwd_crc_sector, default_key, raw_uid) == rfid.OK:
                                    print(f"Authentication for sector {passwd_crc_sector} successful!")

                                    # Write the CRC to the CRC sector
                                    write_status = rfid.write(passwd_crc_sector, crc_bytes + [0x00] * 14)  # Pad to 16 bytes
                                    if write_status == rfid.OK:
                                        print(f"CRC successfully written to sector {passwd_crc_sector}!")
                                        green_led.value = True
                                        return True  # Return True if write is successful
                                    else:
                                        print(f"Failed to write CRC to sector {passwd_crc_sector}.")
                                        red_led.value = True
                                else:
                                    print(f"Authentication for sector {passwd_crc_sector} failed.")
                                    red_led.value = True
                            else:
                                print(f"Failed to write password to sector {passwd_sector}.")
                                red_led.value = True
                        else:
                            print(f"Sector {passwd_sector} is not empty. Cannot write password.")
                            red_led.value = True
                    else:
                        print(f"Authentication for sector {passwd_sector} failed.")
                        red_led.value = True

            rfid.stop_crypto1()

        else:
            print("Failed to read card UID.")
            red_led.value = True


# Main logic
def manage_password(password_to_store):
    # First, try to read the password
    stored_password = read_password_with_crc()
    print("stored_password: %s", stored_password)

    if stored_password:
        print("Password already stored:", stored_password)
    else:
        print("No password stored. Writing new password...")
        if write_password_with_crc(password_to_store):
            print("Password successfully written. Verifying...")
            # Verify the password was written correctly
            stored_password = read_password_with_crc()
            if stored_password == password_to_store:
                print("Password verified and stored successfully!")
            else:
                print("Failed to verify the stored password.")
        else:
            print("Failed to write the password.")

# Example usage
password_to_store = "wtdMY8VSTTQ91qfW"  # Change this to your desired password (max 16 characters)
manage_password(password_to_store)