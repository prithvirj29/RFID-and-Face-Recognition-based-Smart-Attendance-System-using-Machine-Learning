import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522

reader = SimpleMFRC522()

try:
    print("Place your tag to write")
    text = input('Enter text to write: ')
    print("Now place your tag to write")
    reader.write(text)
    print("Written")
    
    print("Place your tag to read")
    id, text = reader.read()
    print(f"ID: {id}")
    print(f"Text: {text}")

finally:
    GPIO.cleanup()
