"""
Improved example of reading from a card using the ``mfrc522`` module.
This script provides detailed information about the RFID card, including its type, size, and whether it is rewritable.
It also reads from block 8 and its 4 sectors.
"""

# 3rd party
import board
import time

# this package
from mfrc522 import MFRC522

# Define SPI pins for RP2040-Zero
sck = board.GP2
mosi = board.GP3
miso = board.GP4
cs = board.GP0
rst = board.GP1

# Initialize MFRC522
rdr = MFRC522(sck, mosi, miso, rst, cs)

# Default key for authentication
default_key = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]

def get_card_type(rdr):
    """
    Determine the type of the RFID card (NTAG, MIFARE, etc.).
    """
    if rdr.IsNTAG():
        if rdr.NTAG == rdr.NTAG_213:
            return "NTAG213"
        elif rdr.NTAG == rdr.NTAG_215:
            return "NTAG215"
        elif rdr.NTAG == rdr.NTAG_216:
            return "NTAG216"
        else:
            return "Unknown NTAG"
    else:
        return "MIFARE Classic"

def get_card_size(rdr):
    """
    Determine the size of the RFID card based on its type.
    """
    if rdr.IsNTAG():
        if rdr.NTAG == rdr.NTAG_213:
            return "144 bytes"
        elif rdr.NTAG == rdr.NTAG_215:
            return "504 bytes"
        elif rdr.NTAG == rdr.NTAG_216:
            return "888 bytes"
        else:
            return "Unknown size"
    else:
        return "1K (1024 bytes) or 4K (4096 bytes)"

def is_card_rewritable(rdr):
    """
    Determine if the card is rewritable or a one-time write card.
    NTAG cards are generally rewritable, while some MIFARE cards may have read-only sectors.
    """
    if rdr.IsNTAG():
        return "Rewritable"
    else:
        return "Rewritable (except for read-only sectors)"

def read_block_and_sectors(rdr, block_addr, key=None, uid=None):
    """
    Read data from a block and its 4 sectors.
    """
    data = []
    for sector in range(4):
        sector_addr = block_addr + sector
        if rdr.IsNTAG():
            # NTAG cards do not require authentication
            sector_data = rdr.read(sector_addr)
        else:
            (stat, tag_type) = rdr.request(rdr.REQIDL)
            if stat == rdr.OK:
                (stat, raw_uid) = rdr.SelectTagSN()

                # MIFARE Classic requires authentication
                if rdr.auth(rdr.AUTHENT1A, sector_addr, key, uid) == rdr.OK:
                    sector_data = rdr.read(sector_addr)
                else:
                    print(f"Authentication failed for sector {sector_addr}.")
                    sector_data = None
        if sector_data:
            data.append((sector_addr, sector_data))
    return data

def do_read():
    print('')
    print("Place card before reader to read from address 0x08 and its 4 sectors.")
    print('')

    try:
        while True:
            # Scan for cards
            (stat, tag_type) = rdr.request(rdr.REQIDL)

            if stat == rdr.OK:
                # Get the UID of the card
                (stat, raw_uid) = rdr.SelectTagSN()

                if stat == rdr.OK:
                    uid_hex = ''.join('{:02X}'.format(x) for x in raw_uid)
                    
                    print("Card UID:", uid_hex)
                    print("  - Tag type: 0x%02x" % tag_type)
                    
                    # Determine card type, size, and rewritability
                    card_type = get_card_type(rdr)
                    card_size = get_card_size(rdr)
                    rewritable = is_card_rewritable(rdr)
                    
                    print(f"  - Card type: {card_type}")
                    print(f"  - Card size: {card_size}")
                    print(f"  - Rewritable: {rewritable}")
                    
                    # Read block 8 and its 4 sectors
                    print("\nReading block 8 and its 4 sectors:")
                    block_data = read_block_and_sectors(rdr, 8, default_key, raw_uid)
                    
                    for sector_addr, sector_data in block_data:
                        print(f"  - Sector {sector_addr}: {sector_data}")
                        if sector_data == [0] * 16:
                            print("    - Sector is empty.")
                        else:
                            try:
                                # Try to decode the data as UTF-8
                                password = bytes(sector_data).decode('utf-8').rstrip('\x00')
                                print(f"    - Decoded data: {password}")
                            except UnicodeError:
                                # If decoding fails, handle the error
                                print("    - Invalid or non-UTF-8 data in sector. Data cannot be decoded as text.")
                                print(f"    - Raw data: {sector_data}")

                    rdr.stop_crypto1()

            time.sleep(1)

    except KeyboardInterrupt:
        print("Bye")

do_read()