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
button = digitalio.DigitalInOut(board.GP14)
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

# Slot system variables
current_slot = 1  # Start with slot 1
max_slots = 15    # Maximum number of slots

def turn_off_all_leds():
    """Turn off all LEDs and reset blinking modes."""
    global blue_blinking, red_blinking
    red_led.value = False
    green_led.value = False
    blue_led.value = False
    blue_blinking = False
    red_blinking = False

def blink_green_led(times):
    """Blink the green LED a specified number of times."""
    for _ in range(times):
        green_led.value = True
        time.sleep(0.2)
        green_led.value = False
        time.sleep(0.2)


print(f"Current slot {current_slot}.")
blink_green_led(current_slot)

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
            # Single click logic
            if blue_blinking or red_blinking:
                # Turn off only blinking LEDs
                print("Single click detected with blinking LEDs. Turning off blinking LEDs.")
                blue_blinking = False
                red_blinking = False
                blue_led.value = False
                red_led.value = False
            elif red_led.value or green_led.value or blue_led.value:
                # Turn off all LEDs and reset to normal operation
                print("Single click detected with LEDs ON. Turning off all LEDs.")
                turn_off_all_leds()
            else:
                # Change slot and blink green LED to indicate the selected slot
                current_slot = (current_slot % max_slots) + 1  # Cycle through slots 1-10
                print(f"Single click detected! Changing to slot {current_slot}.")
                blink_green_led(current_slot)
        elif press_count == 2:
            # Double-click logic
            print("Double-click detected! Blinking blue LED.")
            blue_blinking = True
            red_blinking = False
            green_led.value = False
        elif press_count == 3:
            # Triple-click logic
            print("Triple-click detected! Blinking red LED.")
            red_blinking = True
            blue_blinking = False
            green_led.value = False
        elif press_count == 4:
            # Triple-click logic
            print("Four-click detected! Back to Slot 1.")
            red_blinking = False
            blue_blinking = False
            green_led.value = False
            # Change slot and blink green LED to indicate the selected slot 1
            current_slot = 1
            print(f"Changing to slot {current_slot}.")
            blink_green_led(current_slot)
            current_slot = (current_slot % max_slots) + 1  # Cycle through slots 1-10
        # Reset the press count after evaluating
        press_count = 0

    # Handle blue blinking
    if blue_blinking:
        blue_led.value = not blue_led.value
        time.sleep(0.2)  # Blink every 0.5 seconds

    # Handle red blinking (faster)
    if red_blinking:
        red_led.value = not red_led.value
        time.sleep(0.1)  # Blink every 0.2 seconds

    # Small delay to reduce CPU usage
    time.sleep(0.05)