import time
import board
from mfrc522 import MFRC522
from ndef import NDEF  # Import the NDEF class

# Define SPI pins for RP2040-Zero
sck = board.GP2
mosi = board.GP3
miso = board.GP4
cs = board.GP0
rst = board.GP1

# Initialize MFRC522
rfid = MFRC522(sck, mosi, miso, rst, cs)

# Main loop
while True:
    rfid.init()

    # Scan for cards
    (status, tag_type) = rfid.request(rfid.REQIDL)
    if status == rfid.OK:
        print("Card detected!")

        # Get the UID of the card
        (status, raw_uid) = rfid.SelectTagSN()

        if status == rfid.OK:
            uid_hex = ''.join('{:02X}'.format(x) for x in raw_uid)

            print("Card UID:", uid_hex)
            print("  - tag type: 0x%02x" % tag_type)

            # Encode a text string into an NDEF message
            text = "Hello, CircuitPython!"
            ndef_bytes = NDEF.encode(text, "utf-8")
            print("NDEF Message to Write:", ndef_bytes.hex())

            # Write NDEF data to the tag
            start_page = 4  # Start writing from page 4 (user memory)
            for i in range(0, len(ndef_bytes), 4):
                page_data = ndef_bytes[i:i+4]
                if len(page_data) < 4:
                    page_data += b"\x00" * (4 - len(page_data))  # Pad with zeros
                status = rfid.writeNTAGPage(start_page + i // 4, list(page_data))
                if status != rfid.OK:
                    print("Failed to write NDEF data.")
                    break
            else:
                print("NDEF data written successfully!")

            time.sleep(2)

            # Read NDEF data from the tag
            ndef_bytes = b""
            start_page = 4  # Start reading from page 4 (user memory)
            while True:
                page_data = rfid.readNTAGPage(start_page)
                if page_data == b"\x00\x00\x00\x00":
                    break  # Stop reading if empty page is encountered
                ndef_bytes += bytes(page_data)
                start_page += 1

            if ndef_bytes:
                print("NDEF Message Read:", ndef_bytes.hex())
                decoded_text = NDEF.decode(ndef_bytes)
                if decoded_text:
                    print("Decoded Text:", decoded_text)
                else:
                    print("Failed to decode NDEF message.")
            else:
                print("No valid NDEF message found.")

    time.sleep(5)