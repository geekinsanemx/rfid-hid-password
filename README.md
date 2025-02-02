# RFID Smartcard Reader with RP2040-Zero

This project demonstrates how to use an **RP2040-Zero** microcontroller to read data from an **MFRC522 RFID module** and simulate keyboard input using the `adafruit_hid` library. The project also includes feedback LEDs to indicate the status of the operation.

---

## **Project Structure**
```
rfid-smartcard-reader/
├── clear_rfid_password.py
├── code.py
├── dump-rfid-smartcard.py
├── example-read-improved.py
├── example-read-mfc.py
├── example-read-ntag.py
├── example-read.py
├── example-store-big-password.py
├── lib
│   ├── adafruit_hid
│   ├── adafruit_pn532
│   └── mfrc522.py
├── rfid-hid-password.py
├── rfid-password-manager.py
├── smartcard_dump.py
└── test-rfid-mfrc522.py
├── README.md # Project documentation
└── requirements.txt # List of required libraries
```


---

## **Hardware Setup**

### **RP2040-Zero Pin Connections**

| RP2040-Zero Pin | MFRC522 Pin | LED Pin       | Description                     |
|-----------------|-------------|---------------|---------------------------------|
| **GP2**         | SCK         | -             | SPI Clock                       |
| **GP3**         | MOSI        | -             | SPI Master Out Slave In         |
| **GP4**         | MISO        | -             | SPI Master In Slave Out         |
| **GP0**         | SDA (CS)    | -             | SPI Chip Select                 |
| **GP1**         | RST         | -             | Reset Pin                       |
| **GP5**         | -           | Red LED       | Feedback LED for errors         |
| **GP6**         | -           | Green LED     | Feedback LED for success        |
| **GP7**         | -           | Blue LED      | Feedback LED for device on      |
| **3.3V**        | 3.3V        | -             | Power for MFRC522 and LEDs      |
| **GND**         | GND         | GND           | Ground for MFRC522 and LEDs     |

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
   - Download and install additional libraries for CircuitPython on your RP2040-Zero from the [official website](https://circuitpython.org/libraries).
   - Library mfrc522.py is based in this project which provide a modified version of mfrc522 library from MycroPython for CircuitPython [domdfcoding/circuitpython-mfrc522](https://github.com/domdfcoding/circuitpython-mfrc522/blob/master/mfrc522.py).
     - also added very useful functions from this other mfrc522.py project from MycroPython []().

2. **Install Required Libraries**:
   - Copy the `adafruit_hid` and `mfrc522.py` libraries to the `lib` folder on your RP2040-Zero.

3. **Upload the Code**:
   - Copy the `code.py` file to the root of your RP2040-Zero.

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

---

## **Example Output**
```
When a card is detected and sector 8 is read, the script will print the following output:
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
Password empty.
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

## **License**

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## **Acknowledgments**

- [Adafruit CircuitPython](https://circuitpython.org/) for the HID library.
- [MFRC522 Library](https://github.com/wendlers/micropython-mfrc522) for RFID communication.
- [domdfcoding/circuitpython-mfrc522](https://github.com/domdfcoding/circuitpython-mfrc522).

---

## **Contact**

For questions or feedback, please open an issue on the [GitHub repository](https://github.com/geekinsanemx/rfid-hid-password).
