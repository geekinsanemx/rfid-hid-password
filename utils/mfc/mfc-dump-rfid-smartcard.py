import board
import time
from mfrc522 import MFRC522

# Define SPI pins for RP2040-Zero
sck = board.GP2
mosi = board.GP3
miso = board.GP4
cs = board.GP0
rst = board.GP1

# Initialize MFRC522
rfid = MFRC522(sck, mosi, miso, rst, cs)

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

# Function to check if data is ASCII-readable
def is_ascii_readable(data):
    # Check if all bytes are within the ASCII range (0-127)
    for byte in data:
        if byte > 127 or byte < 32 and byte != 10 and byte != 13:  # Exclude non-printable chars except newline and carriage return
            return None
    try:
        # Attempt to decode as ASCII
        decoded = ''.join([chr(byte) for byte in data if byte != 0])
        return decoded
    except:
        return None

# Function to dump sector and block data
def dump_smartcard_data():
    print("Starting smartcard data dump...")
    print("=============================================")

    # Initialize card detection
    rfid.init()
    (status, tag_type) = rfid.request(rfid.REQIDL)
    if status != rfid.OK:
        print("No card detected. Please place a card near the reader.")
        return

    print("Card detected!")
    (status, raw_uid) = rfid.SelectTagSN()
    if status != rfid.OK:
        print("Failed to select card.")
        return

    uid_hex = ''.join(['{:02X}'.format(x) for x in raw_uid])
    print("Card UID: {}".format(uid_hex))
    print("=============================================")

    # Loop through all sectors and blocks
    for sector in range(16):  # Assuming a MIFARE Classic 1K card (16 sectors)
        print("\nSector {}:".format(sector))
        print("-----------------------------")

        # Authenticate with the default key
        if rfid.auth(rfid.AUTHENT1A, sector * 4, default_key, raw_uid) == rfid.OK:
            print("Authentication successful for sector {}.".format(sector))

            # Loop through all blocks in the sector
            for block in range(4):  # 4 blocks per sector
                block_number = sector * 4 + block
                data = rfid.read(block_number)

                if data is not None:
                    print("Block {} (Sector {}, Block {}):".format(block_number, sector, block))
                    print("  Data (Hex): {}".format(' '.join(['{:02X}'.format(byte) for byte in data])))

                    # Check if data is ASCII-readable
                    ascii_data = is_ascii_readable(data)
                    if ascii_data:
                        print("  Data (ASCII): {}".format(ascii_data))
                    else:
                        print("  Data (ASCII): Not readable")

                    # Highlight special blocks
                    if block_number == 0:
                        print("  ** Manufacturer Block **")
                    elif block % 4 == 3:
                        print("  ** Sector Trailer Block **")
                        print("    Key A: {}".format(' '.join(['{:02X}'.format(byte) for byte in data[:6]])))
                        print("    Access Bits: {}".format(' '.join(['{:02X}'.format(byte) for byte in data[6:10]])))
                        print("    Key B: {}".format(' '.join(['{:02X}'.format(byte) for byte in data[10:16]])))

                    # Identify password slots starting from sector 1 for slot 1
                    if sector >= 1 and block == 0:  # Slot 1 = Sector 1, Slot 2 = Sector 2, etc.
                        slot = sector
                        print("  ** Password Slot {} **".format(slot))
                        if ascii_data:
                            print("    Password: {}".format(ascii_data))
                        else:
                            print("    Password: Not readable or empty")
                else:
                    print("Failed to read block {}.".format(block_number))

            time.sleep(0.2)
        else:
            print("Authentication failed for sector {}.".format(sector))

    print("\nData dump complete.")
    print("=============================================")
    
    # Stop crypto for the current sector
    rfid.stop_crypto1()


# Run the dump function
if __name__ == "__main__":
    dump_smartcard_data()
