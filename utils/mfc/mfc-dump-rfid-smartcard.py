import board
import digitalio
from mfrc522 import MFRC522

# Define SPI pins for RP2040-Zero
sck = board.GP2
mosi = board.GP3
miso = board.GP4
cs = board.GP0
rst = board.GP1

# Initialize MFRC522
rfid = MFRC522(sck, mosi, miso, rst, cs)

# Load default key for authentication
default_key = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]

# Function to check if data is ASCII-readable
def is_ascii_readable(data):
    try:
        decoded = bytes(data).decode('ascii')
        return decoded
    except UnicodeDecodeError:
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

    uid_hex = ''.join('{:02X}'.format(x) for x in raw_uid)
    print(f"Card UID: {uid_hex}")
    print("=============================================")

    # Loop through all sectors and blocks
    for sector in range(16):  # Assuming a MIFARE Classic 1K card (16 sectors)
        print(f"\nSector {sector}:")
        print("-----------------------------")

        # Authenticate with the default key
        if rfid.auth(rfid.AUTHENT1A, sector * 4, default_key, raw_uid) == rfid.OK:
            print(f"Authentication successful for sector {sector}.")

            # Loop through all blocks in the sector
            for block in range(4):  # 4 blocks per sector
                block_number = sector * 4 + block
                data = rfid.read(block_number)

                if data is not None:
                    print(f"Block {block_number} (Sector {sector}, Block {block}):")
                    print(f"  Data (Hex): {' '.join(f'{byte:02X}' for byte in data)}")

                    # Check if data is ASCII-readable
                    # ascii_data = is_ascii_readable(data)
                    if ascii_data:
                        print(f"  Data (ASCII): {ascii_data}")
                    else:
                        print("  Data (ASCII): Not readable")

                    # Highlight special blocks
                    if block_number == 0:
                        print("  ** Manufacturer Block **")
                    elif block % 4 == 3:
                        print("  ** Sector Trailer Block **")
                        print(f"    Key A: {' '.join(f'{byte:02X}' for byte in data[:6])}")
                        print(f"    Access Bits: {' '.join(f'{byte:02X}' for byte in data[6:10])}")
                        print(f"    Key B: {' '.join(f'{byte:02X}' for byte in data[10:16])}")
                else:
                    print(f"Failed to read block {block_number}.")

            # Stop crypto for the current sector
            rfid.stop_crypto1()
        else:
            print(f"Authentication failed for sector {sector}.")

    print("\nData dump complete.")
    print("=============================================")

# Run the dump function
if __name__ == "__main__":
    dump_smartcard_data()