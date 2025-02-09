import time
import board
from mfrc522 import MFRC522
from ndef import NDEF  # Import the NDEF class

# Initialize MFRC522
mfrc522 = MFRC522(board.GP2, board.GP3, board.GP4, board.GP1, board.GP0)

# Define write and read functions for MFRC522
def write_block(block_addr, data):
    return mfrc522.write(block_addr, data) == mfrc522.OK

def read_block(block_addr):
    return mfrc522.read(block_addr)

# Main loop
while True:
    # Encode a text string into an NDEF message
    text = "Hello, CircuitPython!"
    ndef_bytes = NDEF.encode(text, "utf-8")
    print("NDEF Message to Write:", ndef_bytes.hex())

    # Write NDEF data to the tag
    if NDEF.write_ndef_data(ndef_bytes, write_block):
        print("NDEF data written successfully!")
    else:
        print("Failed to write NDEF data.")

    time.sleep(2)

    # Read NDEF data from the tag
    ndef_bytes = NDEF.read_ndef_data(read_block)
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
