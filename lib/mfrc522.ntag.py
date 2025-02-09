"""
CircuitPython Interface for RC522 boards.
"""

# 3rd party
import busio
import digitalio
from adafruit_bus_device.spi_device import SPIDevice
from microcontroller import Pin


class MFRC522:
    """
    CircuitPython Interface for RC522 boards.

    :param sck: The SPI Clock Pin. Typically ``board.SCK``.
    :param mosi: The SPI MOSI Pin. Typically ``board.MOSI``.
    :param miso: The SPI MISO Pin. Typically ``board.MISO``.
    :param rst: The pin connected to the RST terminal on the RC522 board.
    :param cs: The SPI chip select pin, connected to the SDA terminal on the RC522 board.
    """

    DEBUG = 0

    OK = 0
    NOTAGERR = 1
    ERR = 2

    REQIDL = 0x26
    REQALL = 0x52
    AUTHENT1A = 0x60
    AUTHENT1B = 0x61

    NTAG_213 = 213
    NTAG_215 = 215
    NTAG_216 = 216
    NTAG_NONE = 0

    PICC_ANTICOLL1 = 0x93
    PICC_ANTICOLL2 = 0x95
    PICC_ANTICOLL3 = 0x97

    def __init__(self, sck: Pin, mosi: Pin, miso: Pin, rst: Pin, cs: Pin):

        self.cs = digitalio.DigitalInOut(cs)

        self.rst = digitalio.DigitalInOut(rst)
        self.rst.switch_to_output()

        self.rst.value = 0
        self.rst.value = 1

        self.NTAG = 0
        self.NTAG_MaxPage = 0

        self.spi = busio.SPI(sck, MOSI=mosi, MISO=miso)
        self.spi_device = SPIDevice(self.spi, self.cs)

        self.init()

    def _wreg(self, reg: int, val):

        with self.spi_device as bus_device:
            bus_device.write(b'%c' % int(0xff & ((reg << 1) & 0x7e)))
            bus_device.write(b'%c' % int(0xff & val))

    def _rreg(self, reg: int):

        with self.spi_device as bus_device:
            bus_device.write(b'%c' % int(0xff & (((reg << 1) & 0x7e) | 0x80)))
            val = bytearray(1)
            bus_device.readinto(val)

        return val[0]

    def _sflags(self, reg: int, mask: int):
        self._wreg(reg, self._rreg(reg) | mask)

    def _cflags(self, reg: int, mask: int):
        self._wreg(reg, self._rreg(reg) & (~mask))

    def _tocard(self, cmd: int, send):

        recv = []
        bits = irq_en = wait_irq = 0
        stat = self.ERR

        if cmd == 0x0E:
            irq_en = 0x12
            wait_irq = 0x10
        elif cmd == 0x0C:
            irq_en = 0x77
            wait_irq = 0x30

        self._wreg(0x02, irq_en | 0x80)
        self._cflags(0x04, 0x80)
        self._sflags(0x0A, 0x80)
        self._wreg(0x01, 0x00)

        for c in send:
            self._wreg(0x09, c)
        self._wreg(0x01, cmd)

        if cmd == 0x0C:
            self._sflags(0x0D, 0x80)

        i = 2000
        while True:
            n = self._rreg(0x04)
            i -= 1
            if ~((i != 0) and ~(n & 0x01) and ~(n & wait_irq)):
                break

        self._cflags(0x0D, 0x80)

        if i:
            if (self._rreg(0x06) & 0x1B) == 0x00:
                stat = self.OK

                if n & irq_en & 0x01:
                    stat = self.NOTAGERR
                elif cmd == 0x0C:
                    n = self._rreg(0x0A)
                    lbits = self._rreg(0x0C) & 0x07
                    if lbits != 0:
                        bits = (n - 1) * 8 + lbits
                    else:
                        bits = n * 8

                    if n == 0:
                        n = 1
                    elif n > 16:
                        n = 16

                    for _ in range(n):
                        recv.append(self._rreg(0x09))
            else:
                stat = self.ERR

        return stat, recv, bits

    def _crc(self, data):

        self._cflags(0x05, 0x04)
        self._sflags(0x0A, 0x80)

        for c in data:
            self._wreg(0x09, c)

        self._wreg(0x01, 0x03)

        i = 0xFF
        while True:
            n = self._rreg(0x05)
            i -= 1
            if not ((i != 0) and not (n & 0x04)):
                break

        return [self._rreg(0x22), self._rreg(0x21)]

    def init(self):

        self.reset()
        self._wreg(0x2A, 0x8D)
        self._wreg(0x2B, 0x3E)
        self._wreg(0x2D, 30)
        self._wreg(0x2C, 0)
        self._wreg(0x15, 0x40)
        self._wreg(0x11, 0x3D)
        self.antenna_on()

    def reset(self):
        self._wreg(0x01, 0x0F)

    def antenna_on(self, on=True):

        if on and ~(self._rreg(0x14) & 0x03):
            self._sflags(0x14, 0x03)
        else:
            self._cflags(0x14, 0x03)

    def request(self, mode):

        self._wreg(0x0D, 0x07)
        (stat, recv, bits) = self._tocard(0x0C, [mode])

        if (stat != self.OK) | (bits != 0x10):
            stat = self.ERR

        return stat, bits

    def anticoll(self, anticolN = PICC_ANTICOLL1):

        ser_chk = 0
        ser = [anticolN, 0x20]

        self._wreg(0x0D, 0x00)
        (stat, recv, bits) = self._tocard(0x0C, ser)

        if stat == self.OK:
            if len(recv) == 5:
                for i in range(4):
                    ser_chk = ser_chk ^ recv[i]
                if ser_chk != recv[4]:
                    stat = self.ERR
            else:
                stat = self.ERR

        return stat, recv

    def select_tag(self, ser):

        buf = [0x93, 0x70] + ser[:5]
        buf += self._crc(buf)
        (stat, recv, bits) = self._tocard(0x0C, buf)
        return self.OK if (stat == self.OK) and (bits == 0x18) else self.ERR

    def auth(self, mode, addr, sect, ser):
        return self._tocard(0x0E, [mode, addr] + sect + ser[:4])[0]

    def stop_crypto1(self):
        self._cflags(0x08, 0x08)

    def read(self, addr):

        data = [0x30, addr]
        data += self._crc(data)
        (stat, recv, _) = self._tocard(0x0C, data)
        return recv if stat == self.OK else None

    def write(self, addr, data):

        buf = [0xA0, addr]
        buf += self._crc(buf)
        (stat, recv, bits) = self._tocard(0x0C, buf)

        if not (stat == self.OK) or not (bits == 4) or not ((recv[0] & 0x0F) == 0x0A):
            stat = self.ERR
        else:
            buf = []
            for i in range(16):
                buf.append(data[i])
            buf += self._crc(buf)
            (stat, recv, bits) = self._tocard(0x0C, buf)
            if not (stat == self.OK) or not (bits == 4) or not ((recv[0] & 0x0F) == 0x0A):
                stat = self.ERR

        return stat

    def write_block_ntag(self, page, data):
        """
        Write data to a specific page on an NTAG213 tag.
        :param page: The page address to write to (0 to 44 for NTAG213).
        :param data: The data to write (4 bytes).
        :return: True if successful, False otherwise.
        """
        if page < 0 or page > 44:
            print(f"Invalid page address: {page}. Must be between 0 and 44.")
            return False

        # NTAG213 requires 4 bytes of data per page
        if len(data) != 4:
            print("Data must be exactly 4 bytes.")
            return False

        # Write the data to the specified page
        status = self.write(page, data)
        return status == self.OK

    def read_block_ntag(self, page):
        """
        Read data from a specific page on an NTAG213 tag.
        :param page: The page address to read from (0 to 44 for NTAG213).
        :return: The data read (4 bytes), or None if the address is invalid.
        """
        if page < 0 or page > 44:
            print(f"Invalid page address: {page}. Must be between 0 and 44.")
            return None

        # Read the data from the specified page
        data = self.read(page)
        if data is None:
            print("Failed to read data from the tag.")
            return None

        return data

    def set_antenna_gain(self, gain: int):
        """
        Set the MFRC522 Receiver Gain

        :param gain:

        Possible values are:

        * ``0x00 << 4`` -- 000b - 18 dB, minimum
        * ``0x01 << 4`` -- 001b - 23 dB
        * ``0x02 << 4`` -- 010b - 18 dB, it seems 010b is a duplicate for 000b
        * ``0x03 << 4`` -- 011b - 23 dB, it seems 011b is a duplicate for 001b
        * ``0x04 << 4`` -- 100b - 33 dB, average, and typical default
        * ``0x05 << 4`` -- 101b - 38 dB
        * ``0x06 << 4`` -- 110b - 43 dB
        * ``0x07 << 4`` -- 111b - 48 dB, maximum
        * ``0x00 << 4`` -- 000b - 18 dB, minimum, convenience for RxGain_18dB
        * ``0x04 << 4`` -- 100b - 33 dB, average, convenience for RxGain_33dB
        * ``0x07 << 4`` -- 111b - 48 dB, maximum, convenience for RxGain_48dB

        :return:
        """

        # Above table from https://github.com/miguelbalboa/rfid/blob/master/src/MFRC522.h
        # See also 9.3.3.6 / table 98 of the datasheet (http://www.nxp.com/documents/data_sheet/MFRC522.pdf)

        self._cflags(0x26, 0x07 << 4)
        self._sflags(0x26, gain & (0x07 << 4))

    def authKeys(self, uid, addr, keyA=None, keyB=None):
        status = self.ERR
        if keyA is not None:
            status = self.auth(self.AUTHENT1A, addr, keyA, uid)
        elif keyB is not None:
            status = self.auth(self.AUTHENT1B, addr, keyB, uid)
        return status

    def PcdSelect(self, serNum, anticolN):
        backData = []
        buf = []
        buf.append(anticolN)
        buf.append(0x70)

        for i in serNum:
            buf.append(i)

        pOut = self._crc(buf)
        buf.append(pOut[0])
        buf.append(pOut[1])
        (status, backData, backLen) = self._tocard(0x0C, buf)

        if (status == self.OK) and (backLen == 0x18):
            return  1
        else:
            return 0

    def SelectTag(self, uid):
        byte5 = 0

        for i in uid:
            byte5 = byte5 ^ i
        puid = uid + [byte5]

        if self.PcdSelect(puid, self.PICC_ANTICOLL1) == 0:
            return (self.ERR, [])

        return (self.OK, uid)

    def tohexstring(self, v):
        s="["
        for i in v:
            if i != v[0]:
                s = s+ ", "
            s=s+ "0x{:02X}".format(i)
        s= s+ "]"

        return s

    def get_uid(self):
        """
        Retrieve the UID (Unique Identifier) of the RFID/NFC card.

        Returns:
            list: A list of bytes representing the UID of the card.
                  Returns an empty list if no card is detected or an error occurs.
        """
        # Use the SelectTagSN method to get the UID
        status, uid = self.SelectTagSN()

        if status == self.OK:
            return uid  # Return the UID if successful
        else:
            return []  # Return an empty list if no card is detected or an error occurs

    def SelectTagSN(self):
        valid_uid = []
        (status, uid) = self.anticoll(self.PICC_ANTICOLL1)

        if status != self.OK:
            return  (self.ERR, [])

        if self.DEBUG:
            print("anticol(1) {}".format(uid))

        if self.PcdSelect(uid, self.PICC_ANTICOLL1) == 0:
            return (self.ERR, [])

        if self.DEBUG:
            print("pcdSelect(1) {}".format(uid))

        if uid[0] == 0x88 :
            valid_uid.extend(uid[1:4])
            (status, uid) = self.anticoll(self.PICC_ANTICOLL2)
            if status != self.OK:
                return (self.ERR, [])

            if self.DEBUG:
                print("Anticol(2) {}".format(uid))

            rtn =  self.PcdSelect(uid, self.PICC_ANTICOLL2)
            if self.DEBUG:
                print("pcdSelect(2) return={} uid={}".format(rtn, uid))

            if rtn == 0:
                return (self.ERR, [])

            if self.DEBUG:
                print("PcdSelect2() {}".format(uid))

            if uid[0] == 0x88 :
                valid_uid.extend(uid[1:4])
                (status, uid) = self.anticoll(self.PICC_ANTICOLL3)

                if status != self.OK:
                    return (self.ERR, [])

                if self.DEBUG:
                    print("Anticol(3) {}".format(uid))

                if self.PcdSelect(uid, self.PICC_ANTICOLL3) == 0:
                    return (self.ERR, [])

                if self.DEBUG:
                    print("PcdSelect(3) {}".format(uid))

        valid_uid.extend(uid[0:5])

        return (self.OK, valid_uid[:len(valid_uid) - 1])

    def writeSectorBlock(self, uid, sector, block, data, keyA=None, keyB=None):
        absoluteBlock =  sector * 4 + (block % 4)

        if absoluteBlock > 63 :
            return self.ERR

        if len(data) != 16:
            return self.ERR

        if self.authKeys(uid, absoluteBlock, keyA, keyB) != self.ERR :
            return self.write(absoluteBlock, data)

        return self.ERR

    def readSectorBlock(self, uid, sector, block, keyA=None, keyB=None):
        absoluteBlock =  sector * 4 + (block % 4)

        if absoluteBlock > 63 :
            return self.ERR, None

        if self.authKeys(uid, absoluteBlock, keyA, keyB) != self.ERR :
            return self.read(absoluteBlock)

        return self.ERR, None

    def MFRC522_DumpClassic1K(self, uid, Start=0, End=64, keyA=None, keyB=None):
        for absoluteBlock in range(Start, End):
            status = self.authKeys(uid, absoluteBlock, keyA, keyB)

            print("{:02d} S{:02d} B{:1d}: ".format(absoluteBlock, absoluteBlock//4 , absoluteBlock % 4),end="")

            if status == self.OK:
                block = self.read(absoluteBlock)

                if status == self.ERR:
                    break

                else:
                    for value in block:
                        print("{:02X} ".format(value),end="")

                    print("  ", end="")

                    for value in block:
                        if (value > 0x20) and (value < 0x7f):
                            print(chr(value), end="")
                        else:
                            print('.', end="")

                    print("")
            else:
                break

        if status == self.ERR:
            print("Authentication error")
            return self.ERR

        return self.OK

    def MFRC522_Dump_NTAG(self, Start=0, End=135):
        for absoluteBlock in range(Start, End, 4):
            MaxIndex = 4 * 135
            status = self.OK
            print("Page {:02d}: ".format(absoluteBlock), end="")
            if status == self.OK:
                block = self.read(absoluteBlock)
                if status == self.ERR:
                    break

                else:
                    Index = absoluteBlock*4

                    for i in range(len(block)):
                        if Index < MaxIndex :
                           print("{:02X} ".format(block[i]), end="")

                        else:
                           print("   ", end="")

                        if (i%4)==3:
                           print(" ", end="")

                        Index+=1
                    print("  ", end="")

                    Index = absoluteBlock*4

                    for value in block:
                        if Index < MaxIndex:
                            if (value > 0x20) and (value < 0x7f):
                                print(chr(value), end="")
                            else:
                                print('.',end="")

                        Index+=1
                    print("")
            else:
                break

        if status == self.ERR:
            print("Authentication error")
            return self.ERR

        return self.OK

    def writeNTAGPage(self, page, data):
        if page > self.NTAG_MaxPage:
            return self.ERR

        if page < 4:
            return self.ERR

        if len(data) != 4:
            return self.ERR

        return self.write(page, data+[0]*12)

    def readNTAGPage(self, page):
        """
        Read data from a specific page on an NTAG213 tag.
        :param page: The page address to read from (0 to 44 for NTAG213).
        :return: The data read (4 bytes), or None if the address is invalid.
        """
        if page < 0 or page > 44:
            print(f"Invalid page address: {page}. Must be between 0 and 44.")
            return None

        # Read the data from the specified page
        data = self.read(page)
        if data is None:
            print("Failed to read data from the tag.")
            return None

        return data

    def getNTAGVersion(self):
         buf = [0x60]
         buf += self._crc(buf)
         stat, recv, _ = self._tocard(0x0C, buf)
         return stat, recv

    #Version NTAG213 = [0x0 ,0x4, 0x4, 0x2, 0x1, 0x0,0x0f, 0x3]
    #Version NTAG215 = [0x0 ,0x4, 0x4, 0x2, 0x1, 0x0,0x11, 0x3]
    #Version NTAG216 = [0x0 ,0x4, 0x4, 0x2, 0x1, 0x0,0x13, 0x3]

    def IsNTAG(self):
        self.NTAG = self.NTAG_NONE
        self.NTAG_MaxPage=0
        (stat, rcv) = self.getNTAGVersion()

        if stat == self.OK:
            if len(rcv) < 8:
                return False  #do we have at least 8 bytes

            if rcv[0] != 0:
                return False  #check header

            if rcv[1] != 4:
                return False  #check Vendor ID

            if rcv[2] != 4:
                return False  #check product type

            if rcv[3] != 2:
                return False  #check subtype

            if rcv[7] != 3:
                return False  #check protocol

            if rcv[6] == 0xf:
                self.NTAG= self.NTAG_213
                self.NTAG_MaxPage = 44
                return True

            if rcv[6] == 0x11:
                self.NTAG= self.NTAG_215
                self.NTAG_MaxPage = 134
                return True

            if rcv[7] == 0x13:
                self.NTAG= self.NTAG_216
                self.NTAG_MaxPage = 230
                return True

        return False
