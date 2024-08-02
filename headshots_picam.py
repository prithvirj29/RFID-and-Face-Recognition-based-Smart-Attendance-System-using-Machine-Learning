import cv2
from picamera import PiCamera
from picamera.array import PiRGBArray
import os

# Take name input from the user
name = input("Enter your name: ")

# Ensure the directory for the user's name exists
directory = f"dataset/{name}"
if not os.path.exists(directory):
    os.makedirs(directory)

# Initialize the camera
cam = PiCamera()
cam.resolution = (512, 304)
cam.framerate = 10
rawCapture = PiRGBArray(cam, size=(512, 304))

img_counter = 0

while True:
    for frame in cam.capture_continuous(rawCapture, format="bgr", use_video_port=True):
        image = frame.array
        cv2.imshow("Press Space to take a photo", image)
        rawCapture.truncate(0)
    
        k = cv2.waitKey(1)
        rawCapture.truncate(0)
        if k % 256 == 27:  # ESC pressed
            break
        elif k % 256 == 32:
            # SPACE pressed
            img_name = f"{directory}/image_{img_counter}.jpg"
            cv2.imwrite(img_name, image)
            print(f"{img_name} written!")
            img_counter += 1
            
    if k % 256 == 27:
        print("Escape hit, closing...")
        break

cv2.destroyAllWindows()
