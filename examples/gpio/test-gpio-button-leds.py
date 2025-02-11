import board
import digitalio
import time

# Initialize LEDs
red_led = digitalio.DigitalInOut(board.GP27)
red_led.direction = digitalio.Direction.OUTPUT
green_led = digitalio.DigitalInOut(board.GP28)
green_led.direction = digitalio.Direction.OUTPUT
blue_led = digitalio.DigitalInOut(board.GP29)
blue_led.direction = digitalio.Direction.OUTPUT

# Turn off LEDs initially
red_led.value = False
green_led.value = False
blue_led.value = False

# Initialize button (connected to GPIO 14 and GND)
button = digitalio.DigitalInOut(board.GP15)
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.UP  # Enable internal pull-up resistor

# Variables to track button state and timing
button_was_pressed = False
last_press_time = 0
press_count = 0
click_time_frame = 1  # 1-second frame to count clicks

# Variables for LED modes
blue_blinking = False
red_blinking = False

def turn_off_all_leds():
    """Turn off all LEDs and reset blinking modes."""
    red_led.value = False
    green_led.value = False
    blue_led.value = False
    global blue_blinking, red_blinking
    blue_blinking = False
    red_blinking = False

while True:
    # Check if the button is pressed (button.value is False when pressed)
    if not button.value:
        if not button_was_pressed:
            # Button was just pressed
            button_was_pressed = True
            press_count += 1
            last_press_time = time.monotonic()
            print(f"Button pressed! Press count: {press_count}")  # Debugging
    else:
        if button_was_pressed:
            # Button was just released
            button_was_pressed = False
            print("Button released!")  # Debugging

    # Check if the time frame for counting clicks has passed
    if time.monotonic() - last_press_time > click_time_frame and press_count > 0:
        # Evaluate the number of clicks within the time frame
        if press_count == 1:
            if red_led.value or green_led.value or blue_led.value or blue_blinking or red_blinking:
                print("Single click detected with LEDs ON or blinking. Turning off all LEDs.")
                turn_off_all_leds()
            else:
                print("Single click detected! Turning on green LED.")
                green_led.value = True
        elif press_count == 2:
            print("Double-click detected! Blinking blue LED.")
            blue_blinking = True
            red_blinking = False
            green_led.value = False
        elif press_count == 3:
            print("Triple-click detected! Blinking red LED.")
            red_blinking = True
            blue_blinking = False
            green_led.value = False

        # Reset the press count after evaluating
        press_count = 0

    # Handle blue blinking
    if blue_blinking:
        blue_led.value = not blue_led.value
        time.sleep(0.5)  # Blink every 0.5 seconds

    # Handle red blinking (faster)
    if red_blinking:
        red_led.value = not red_led.value
        time.sleep(0.2)  # Blink every 0.2 seconds

    # Small delay to reduce CPU usage
    time.sleep(0.05)