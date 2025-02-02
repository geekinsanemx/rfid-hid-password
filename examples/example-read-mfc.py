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

        (stat, raw_uid) = rdr.anticoll()

        if stat == rdr.OK:
          print("New card detected")
          print("  - tag type: 0x%02x" % tag_type)
          print("  - uid\t : 0x%02x%02x%02x%02x" % (raw_uid[0], raw_uid[1], raw_uid[2], raw_uid[3]))
          print('')

          if rdr.select_tag(raw_uid) == rdr.OK:

            key = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]

            if rdr.auth(rdr.AUTHENT1A, 8, key, raw_uid) == rdr.OK:
              print("Address 8 data: %s" % rdr.read(8))
              print("Address 9 data: %s" % rdr.read(9))
              

              rdr.stop_crypto1()
            else:
              print("Authentication error")
          else:
            print("Failed to select tag")
        
        time.sleep(1)

  except KeyboardInterrupt:
    print("Bye")

do_read()

