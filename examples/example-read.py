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

# Default key for authentication
default_key = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]

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
                        data = rdr.read(8)
                        
                        print(list(data))
                        
                        if list(data) == [0] * 16:  # Check if the block is empty
                            print("Block is empty.")
                            print(uid_hex)  # Output the UID as keyboard input

                        else:
                            password = bytes(data).decode().rstrip('\x00')
                            print("Password Retrieved. Typing password...")
                            print(password)  # Type the password as keyboard input
                    
                    else:
                        (stat, tag_type) = rdr.request(rdr.REQIDL)
                        if stat == rdr.OK:
                            (stat, raw_uid) = rdr.SelectTagSN()
                            if stat == rdr.OK:
                                
                                if rdr.auth(rdr.AUTHENT1A, 8, default_key, raw_uid) == rdr.OK:
                                    data = rdr.read(8)
                                    
                                    print(list(data))
                                    
                                    if list(data) == [0] * 16:  # Check if the block is empty
                                        print("Block is empty.")
                                        print(uid_hex)  # Output the UID as keyboard input

                                    else:
                                        password = bytes(data).decode().rstrip('\x00')
                                        print("Password Retrieved. Typing password...")
                                        print(password)  # Type the password as keyboard input
                                        
                                else:
                                    print("Authentication failed.")
                                    
                            else:
                                print("Failed to read card.")
                                
                    rdr.stop_crypto1()

            time.sleep(1)

    except KeyboardInterrupt:
        print("Bye")

do_read()