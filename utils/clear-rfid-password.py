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

def clear_sectors():
    # Main loop
    print("Waiting for RFID/NFC card to clear sectors 8 and 9...")
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

            # Check if the card is an NTAG
            if rfid.IsNTAG():
                print("Detected NTAG card. Skipping authentication.")

                # Clear sector 8
                write_status = rfid.write(8, [0x00] * 16)  # Write 16 zeros to sector 8
                if write_status == rfid.OK:
                    print("Sector 8 cleared successfully!")

                    # Clear sector 9
                    write_status = rfid.write(9, [0x00] * 16)  # Write 16 zeros to sector 9
                    if write_status == rfid.OK:
                        print("Sector 9 cleared successfully!")
                        green_led.value = True
                    else:
                        print("Failed to clear sector 9.")
                        red_led.value = True
                else:
                    print("Failed to clear sector 8.")
                    red_led.value = True

            else:
                print("Detected non-NTAG card. Authenticating...")
                (stat, tag_type) = rfid.request(rfid.REQIDL)
                if stat == rfid.OK:
                    (stat, raw_uid) = rfid.SelectTagSN()

                    # Authenticate with the default key for sector 8
                    if rfid.auth(rfid.AUTHENT1A, 8, default_key, raw_uid) == rfid.OK:
                        print("Authentication for sector 8 successful!")

                        # Clear sector 8
                        write_status = rfid.write(8, [0x00] * 16)  # Write 16 zeros to sector 8
                        if write_status == rfid.OK:
                            print("Sector 8 cleared successfully!")

                            # Authenticate with the default key for sector 9
                            if rfid.auth(rfid.AUTHENT1A, 9, default_key, raw_uid) == rfid.OK:
                                print("Authentication for sector 9 successful!")

                                # Clear sector 9
                                write_status = rfid.write(9, [0x00] * 16)  # Write 16 zeros to sector 9
                                if write_status == rfid.OK:
                                    print("Sector 9 cleared successfully!")
                                    green_led.value = True
                                else:
                                    print("Failed to clear sector 9.")
                                    red_led.value = True
                            else:
                                print("Authentication for sector 9 failed.")
                                red_led.value = True
                        else:
                            print("Failed to clear sector 8.")
                            red_led.value = True
                    else:
                        print("Authentication for sector 8 failed.")
                        red_led.value = True

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
