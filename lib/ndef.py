class NDEF:
    """
    Minimal NDEF encoder and decoder for CircuitPython.
    Supports encoding/decoding text strings with character encoding.
    """

    @staticmethod
    def encode(text, encoding="utf-8"):
        """
        Encode a text string into an NDEF byte array.
        :param text: The text to encode.
        :param encoding: The character encoding ("utf-8" or "utf-16").
        :return: Bytes representing the NDEF text record.
        """
        # Validate encoding
        if encoding not in ["utf-8", "utf-16"]:
            raise ValueError("Unsupported encoding. Use 'utf-8' or 'utf-16'.")

        # NDEF record header
        record_header = bytearray([0xD1])  # MB=1, ME=1, CF=0, SR=1, IL=0, TNF=1 (NFC Forum well-known type)
        record_header.append(0x01)  # Type Length (1 byte for "T")
        record_header.append(1 + len(text.encode(encoding)))  # Payload Length (1 byte for encoding + text)
        record_header.append(0x54)  # Type ("T" for Text)

        # Encoding and text
        encoding_byte = 0x00 if encoding == "utf-8" else 0x80  # Bit 7: 0 for UTF-8, 1 for UTF-16
        payload = bytearray([encoding_byte])  # Encoding byte (language code length = 0)
        payload += text.encode(encoding)  # Text

        # Combine into NDEF message
        ndef_message = record_header + payload
        return ndef_message

    @staticmethod
    def decode(ndef_bytes):
        """
        Decode an NDEF byte array into a text string.
        :param ndef_bytes: The NDEF message as bytes.
        :return: The decoded text string, or None if invalid.
        """
        if len(ndef_bytes) < 5:
            return None  # Invalid NDEF message

        # Extract record header
        record_header = ndef_bytes[0]
        type_length = ndef_bytes[1]
        payload_length = ndef_bytes[2]
        record_type = ndef_bytes[3]

        # Extract payload
        payload = ndef_bytes[4:4 + payload_length]

        # Decode based on record type
        if record_type == 0x54:  # Text record
            encoding_byte = payload[0]
            encoding = "utf-16" if (encoding_byte & 0x80) else "utf-8"  # Check bit 7
            text = payload[1:].decode(encoding)  # Decode text
            return text
        else:
            return None  # Unsupported record type

    @staticmethod
    def write_ndef_data(ndef_bytes, write_function, start_block=4):
        """
        Write NDEF data to a tag using a provided write function.
        :param ndef_bytes: The NDEF data as bytes.
        :param write_function: A function that writes data to a specific block (e.g., mfrc522.write).
        :param start_block: The starting block address for writing (default is 4).
        :return: True if successful, False otherwise.
        """
        block_addr = start_block
        for i in range(0, len(ndef_bytes), 4):
            block_data = ndef_bytes[i:i+4]
            if len(block_data) < 4:
                block_data += b"\x00" * (4 - len(block_data))  # Pad with zeros
            if not write_function(block_addr, block_data):
                return False  # Write failed
            block_addr += 1
        return True  # Write successful

    @staticmethod
    def read_ndef_data(read_function, start_block=4):
        """
        Read NDEF data from a tag using a provided read function.
        :param read_function: A function that reads data from a specific block (e.g., mfrc522.read).
        :param start_block: The starting block address for reading (default is 4).
        :return: The NDEF data as bytes, or None if reading fails.
        """
        ndef_bytes = b""
        block_addr = start_block
        while True:
            block_data = read_function(block_addr)
            if block_data == b"\x00\x00\x00\x00":
                break  # Stop reading if empty block is encountered
            ndef_bytes += block_data
            block_addr += 1
        return ndef_bytes
