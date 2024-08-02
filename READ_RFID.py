import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import time

reader = SimpleMFRC522()

try:
    while True:
        print("Place your tag to read")
        id, text = reader.read()
        print(f"ID: {id}")
        print(f"Text: {text}")
        print("Waiting for the next tag...")

        # Delay before the next read
        time.sleep(1)  # Adjust the delay as needed (2 seconds in this example)

except KeyboardInterrupt:
    print("Exiting the loop and cleaning up...")
finally:
    GPIO.cleanup()


