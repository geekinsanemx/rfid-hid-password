"""
Example of reading from a card using the ``mfrc522`` module.
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


def do_read():

    print('')
    print("Place card before reader to read from address 0x08")
    print('')

    try:
        while True:

            (stat, tag_type) = rdr.request(rdr.REQIDL)

            if stat == rdr.OK:

                (stat, raw_uid) = rdr.SelectTagSN()

                if stat == rdr.OK:
                    uid_hex = ''.join('{:02X}'.format(x) for x in raw_uid)
                    
                    print("Card UID:", uid_hex)
                    print("  - tag type: 0x%02x" % tag_type)
                    
                    if rdr.IsNTAG():
                        print("Got NTAG{}".format(rdr.NTAG))
                        
                        sector8_data = rdr.read(8)
                        sector8_value = ''.join('{:02X}'.format(x) for x in sector8_data)
                        sector9_data = rdr.read(9)
                        sector9_value = ''.join('{:02X}'.format(x) for x in sector9_data)
                        
                        print("Address 8 data: %s" % sector8_data)
                        print("Address 8 value: %s" % sector8_value)
                        print("Address 9 data: %s" % sector9_data)
                        print("Address 9 value: %s" % sector9_value)

                        if list(sector8_data) == [0] * 16:  # Check if the block is empty
                            print("Block is empty.")
                            print(uid_hex)  # Output the UID as keyboard input

                        else:
                            password = bytes(sector8_data).decode('utf-8').rstrip('\x00')
                            print("Password Retrieved. Typing password...")
                            print(password)  # Type the password as keyboard input

            time.sleep(1)

    except KeyboardInterrupt:
        print("Bye")

do_read()



