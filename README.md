# RFID Smartcard Reader with RP2040-Zero

I wanted to store a big and secure password in a "secure way" and type it into the computer... but 16 or more special characters?? So I was thinking of storing the password in an RFID card and using it as a password in my case to encrypt/decrypt/open a LUKS partition, etc.

In theory, it's almost easy to store data into an RFID card or tag, but often the only possible way to use that info is in the application reader or specific purpose application, which in my case does not fit with the *enter luks password:* prompt to decrypt a partition, so I thought what I needed was a device to read the password from the RFID card/tag and type it into the computer as a keyboard, no matter what is on the screen, just type it ...

I know the security implications of leaving the card/tag unprotected or laying around with physical access or reading for others. I'm thinking of implementing more secure ways to store the data on the card (avoiding others with physical access to obtain the password) and adding validation so you're the one and only one who is reading the password. Please refer to the [**Features pending to add**](#features-pending-to-add) and if you want and can contribute, you're welcome!! :)

This project demonstrates how to use an **RP2040-Zero** microcontroller to read data from an **MFRC522 RFID module** and simulate keyboard input using the `adafruit_hid` library. The project also includes feedback LEDs to indicate the status of the operation.

![image](https://github.com/user-attachments/assets/f9915e8d-110c-4d38-8286-22f905c7ce35)

---

## **Project Structure**
```
rfid-smartcard-reader/
.
├── default_key.json
├── rfid-hid-password.py
|
├── examples
│   ├── example-read.py
│   ├── mfc
│   │   └── example-read-mfc.py
│   ├── ntag
│   │   └── example-read-ntag.py
│   ├── test-gpio-leds.py
│   └── test-rfid-hid-input.py
|
├── lib
│   ├── adafruit_hid
│   └── mfrc522.py
|
└── utils
    ├── clear-rfid-password.py
    ├── mfc
    │   ├── mfc-dump-rfid-smartcard.py
    │   └── mfc-store-big-password.py
    ├── ntag
    │   └── ntag-dump-rfid-smartcard.py
    ├── store-rfid-password.py
    └── validate-key-file.py


```
---

## **Hardware Setup**

### **Connecting the MFRC522 to RP2040-Zero:**
    SDA/CS: Connect SDA on MFRC522 to GP0 on RP2040-Zero.
    RST: Connect RST on MFRC522 to GP1 on RP2040-Zero.
    SCK: Connect SCK on MFRC522 to GP2 on RP2040-Zero.
    MOSI: Connect MOSI on MFRC522 to GP3 on RP2040-Zero.
    MISO: Connect MISO on MFRC522 to GP4 on RP2040-Zero.

    GND: Connect a GND from the MFRC522 to one of the GND pins on the RP2040-Zero.
    3.3V: Connect the 3.3V pin from the MFRC522 to one of the 3.3V pins on RP2040-Zero.

### **Connecting LEDs to RP2040-Zero:**
    220-ohm resistor with a tolerance of ±5% would be color-coded: Red, Red, Brown, Gold.

    Green LED (Access Granted):
        Anode (longer leg) connects to GP27 on RP2040-Zero.
        Cathode (shorter leg) connects through a 220-ohm resistor to a GND pin on RP2040-Zero.

    Red LED (Unauthorized Access):
        Anode (longer leg) connects to GP28 on RP2040-Zero.
        Cathode (shorter leg) connects through a 220-ohm resistor to a GND pin on RP2040-Zero.

    Blue LED (Device Ready):
        Anode (longer leg) connects to GP29 on RP2040-Zero.
        Cathode (shorter leg) connects through a 220-ohm resistor to a GND pin on RP2040-Zero.


RP2040-Zero Board
```
│
├─ GP0 ─> SDA (MFRC522 Module)
├─ GP1 ─> RST (MFRC522 Module)
├─ GP2 ─> SCK (MFRC522 Module)
├─ GP3 ─> MOSI (MFRC522 Module)
├─ GP4 ─> MISO (MFRC522 Module)
│
├─ 3V3 ─> 3.3V (MFRC522 Module)
├─ GND ─> GND (MFRC522 Module)
│
├─ GP27 ─> [Green LED] --> [220-ohm Resistor] ---> GND
└─ GP28 ─> [Red LED]  ---> [220-ohm Resistor] ---> GND
└─ GP29 ─> [Blue LED] ---> [220-ohm Resistor] ---> GND
```

### **RP2040-Zero Pin Connections**
```
| RP2040-Zero Pin | MFRC522 Pin | LED Pin       | Description                     |
|-----------------|-------------|---------------|---------------------------------|
| **GP2**         | SCK         | -             | SPI Clock                       |
| **GP3**         | MOSI        | -             | SPI Master Out Slave In         |
| **GP4**         | MISO        | -             | SPI Master In Slave Out         |
| **GP0**         | SDA (CS)    | -             | SPI Chip Select                 |
| **GP1**         | RST         | -             | Reset Pin                       |
| **GP27**        | -           | Red LED       | Feedback LED for errors         |
| **GP28**        | -           | Green LED     | Feedback LED for success        |
| **GP29**        | -           | Blue LED      | Feedback LED for device on      |
| **3.3V**        | 3.3V        | -             | Power for MFRC522 and LEDs      |
| **GND**         | GND         | GND           | Ground for MFRC522 and LEDs     |
```
---

## **LED Feedback**

- **Green LED**:
  - Turns on when the RFID card is successfully authenticated, and the password is read and typed out.

- **Red LED**:
  - Turns on in the following cases:
    - Authentication failure.
    - Invalid data in sector 8.
    - Empty or blank password.
    - Failure to read the card UID.

- **Blue LED**:
  - Turns on when the device is powered on and ready.

---

## **How It Works**

1. **Card Detection**:
   - The RP2040-Zero scans for RFID/NFC cards using the MFRC522 module.

2. **UID Retrieval**:
   - If a card is detected, the UID is retrieved and printed.

3. **Sector 8 Authentication**:
   - The script authenticates sector 8 using the default key (`0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF`).

4. **Password or UID Typing**:
   - If sector 8 contains a valid password, it is typed out as keyboard input.
   - If sector 8 is empty or blank, the script types the UID instead.

5. **Fallback to UID**:
   - If authentication or reading fails, the script falls back to typing the UID.

---

## **Installation**

1. **Install CircuitPython**:
   - Download and install CircuitPython on your RP2040-Zero from the [official website](https://circuitpython.org/board/waveshare_rp2040_zero/).

2. **Install Required Libraries**:
   - Download the [CircuitPython Library Bundle](https://circuitpython.org/libraries).
   - Copy the `adafruit_hid` library to the `lib` folder on your RP2040-Zero.
   - Use the modified `mfrc522.py` library provided in this project, which is based on [domdfcoding/circuitpython-mfrc522](https://github.com/domdfcoding/circuitpython-mfrc522/blob/master/mfrc522.py).

3. **Upload the Code**:
   - Copy the `rfid-hid-password.py` file to the root of your RP2040-Zero.

4. **Connect the Hardware**:
   - Connect the MFRC522 module and LEDs to the RP2040-Zero as described in the pin connections table.

---

## **Usage**

1. **Power On**:
   - Power on the RP2040-Zero and wait for the script to initialize.

2. **Scan a Card**:
   - Place an RFID card near the MFRC522 module.
   - The script will read the card's UID and attempt to authenticate sector 8.

3. **Keyboard Input**:
   - If sector 8 contains a valid password, it will be typed out as keyboard input.
   - If sector 8 is empty or blank, the UID will be typed out instead.

4. **LED Feedback**:
   - The green LED will turn on for successful operations.
   - The red LED will turn on for errors or failures.
   - The blue LED indicates the device is powered on and ready.

---

## **Example Output**

When a card is detected and sector 8 is read, the script will print the following output:
```
Card detected!
Card UID: 4A3B2C1D
Authentication successful!
Password retrieved from sector 8: mypassword123
```
If sector 8 is empty or blank, the script will print:
```
Card detected!
Card UID: 4A3B2C1D
Authentication successful!
Password empty. Typing UID instead.
```
---

## **Troubleshooting**

1. **No Card Detected**:
   - Ensure the card is properly positioned and within range of the MFRC522 module.

2. **Authentication Failures**:
   - Verify that the default key (`0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF`) is correct for the card.

3. **Read Failures**:
   - If reading fails for certain blocks, verify that the blocks are not write-protected or corrupted.

4. **Multiple Reads**:
   - Increase the `time.sleep(1)` delay in the script if it reads the same card multiple times.

---

## **Features pending to add**
* password be stored encrypted and use the tag uid as encryption key in this way even if card data is cloned in another card, cannot be decrypted
* password be stored encrypted using public/private key algoritm
* store password bigger than 16 chars, use multiple blocks for store/reading
* add interactive button to change reading/typing mode to create/store password mode (to create new tags)
* add an MFA mechanism
* use different sectors to store different passwords, (find a way to specify which password to use)

---

## **License**

This project is licensed under the **GNU GENERAL PUBLIC LICENSE**. See the [LICENSE](LICENSE) file for details.

---

## **Acknowledgments**

- [Adafruit CircuitPython](https://circuitpython.org/) for the HID library.
- [MFRC522 Library](https://github.com/wendlers/micropython-mfrc522) for RFID communication.
- [domdfcoding/circuitpython-mfrc522](https://github.com/domdfcoding/circuitpython-mfrc522) for the modified MFRC522 library.

---

## **Contact**

For questions or feedback, please open an issue on the [GitHub repository](https://github.com/geekinsanemx/rfid-hid-password).
