import board
import digitalio
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

# Default key for authentication
default_key = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]

def dump_smartcard(rfid, key):
    """Dump the content of all sectors of the smartcard."""
    print("Dumping smartcard content:")

    # Get the UID of the card
    (status, raw_uid) = rfid.SelectTagSN()
    if status == rfid.OK:
        uid_hex = ''.join('{:02X}'.format(x) for x in raw_uid)
        print("Card UID:", uid_hex)
        
        if rfid.IsNTAG():
            print("Got NTAG{}".format(rfid.NTAG))
            rfid.MFRC522_Dump_NTAG()
                    
        else:
            (stat, tag_type) = rfid.request(rfid.REQIDL)
            if stat == rfid.OK:
                (stat, raw_uid) = rfid.SelectTagSN()
                if stat == rfid.OK:
                    rfid.MFRC522_DumpClassic1K(raw_uid, keyA=key)
                    
        # Stop crypto
        rfid.stop_crypto1()
        
    else:
        print("Failed to read card UID.")

# Main loop
print("Waiting for RFID/NFC card...")
while True:
    # Scan for cards
    (status, tag_type) = rfid.request(rfid.REQIDL)
    if status == rfid.OK:
        print("Card detected!")
        dump_smartcard(rfid, default_key)
        print("")
        
    time.sleep(2)
