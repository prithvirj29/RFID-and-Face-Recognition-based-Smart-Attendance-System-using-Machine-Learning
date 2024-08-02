# Import necessary libraries
import pygsheets  # For interacting with Google Sheets
from datetime import datetime  # For date and time operations
import cv2  # OpenCV for image processing
import face_recognition  # For facial recognition operations
import pickle  # For serializing and deserializing Python objects
import time  # For time-related functions
import RPi.GPIO as GPIO  # For interacting with the GPIO pins on a Raspberry Pi
from mfrc522 import SimpleMFRC522  # For interacting with the MFRC522 RFID module

# Initialize RFID reader
reader = SimpleMFRC522()

# Initialize 'currentname' to trigger only when a new person is identified
currentname = "unknown"

# Load encodings
encodingsP = "encodings.pickle"
print("[INFO] loading encodings + face detector...")
with open(encodingsP, "rb") as file:  # Open the pickle file containing the facial encodings
    data = pickle.load(file)  # Load the facial encodings data

# Initialize the video stream from the webcam and allow the camera sensor to warm up
print("[INFO] starting video stream...")
vs = cv2.VideoCapture(0)  # Start capturing video from the webcam
time.sleep(2.0)  # Wait for 2 seconds to allow the camera to warm up

# Check if the video stream is successfully opened
if not vs.isOpened():
    print("[ERROR] Unable to access the camera.")
    exit()

# Set camera resolution (optional)
vs.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # Set the width of the video frame
vs.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)  # Set the height of the video frame

# Google Sheets setup
gc = pygsheets.authorize(service_file='service_account.json')  # Authorize access to Google Sheets
sh = gc.open('attendance')  # Open the Google Sheet named 'attendance'
sheet = sh.sheet1  # Access the first sheet in the Google Sheet

# Attendance logging function
def log_attendance(name, rfid_id):
    current_datetime = datetime.now()  # Get the current date and time
    date = current_datetime.strftime("%Y-%m-%d")  # Format the date
    time = current_datetime.strftime("%H:%M:%S")  # Format the time
    sheet.append_table([date, time, name, rfid_id])  # Append the attendance data to the Google Sheet

# Start the FPS counter
fps = 0  # Initialize the FPS counter
start_time = time.time()  # Record the start time

# Loop over frames from the video file stream
while True:
    ret, frame = vs.read()  # Read a frame from the video stream
    if not ret:  # Check if the frame was successfully captured
        print("[ERROR] No frame captured from the video stream.")
        break

    frame = cv2.resize(frame, (500, int(frame.shape[0] * 500 / frame.shape[1])))  # Resize the frame

    boxes = face_recognition.face_locations(frame)  # Detect the face locations in the frame
    encodings = face_recognition.face_encodings(frame, boxes)  # Compute the facial encodings for the detected faces
    names = []  # List to store the names of recognized faces

    for encoding in encodings:  # Loop over each facial encoding
        matches = face_recognition.compare_faces(data["encodings"], encoding)  # Compare the encoding with known encodings
        name = "Unknown"  # Default name if no match is found

        if True in matches:  # If a match is found
            matchedIdxs = [i for (i, b) in enumerate(matches) if b]  # Get the indices of matched encodings
            counts = {}  # Dictionary to count the occurrences of each name

            for i in matchedIdxs:  # Loop over matched indices
                name = data["names"][i]  # Get the name corresponding to the matched encoding
                counts[name] = counts.get(name, 0) + 1  # Increment the count for the name

            name = max(counts, key=counts.get)  # Get the name with the highest count

            if currentname != name:  # Check if the recognized name is different from the current name
                currentname = name  # Update the current name
                print(f"Recognized: {currentname}")  # Print the recognized name

                attempts = 0  # Initialize attempt counter
                max_attempts = 3  # Maximum number of attempts allowed

                while attempts < max_attempts:  # Loop for RFID attempts
                    print("Hold your RFID tag near the reader")
                    try:
                        rfid_id, rfid_text = reader.read()  # Read the RFID tag
                        print(f"RFID ID: {rfid_id}, Text: {rfid_text}")

                        if currentname == rfid_text.strip():  # Check if the RFID text matches the recognized name
                            log_attendance(currentname, rfid_id)  # Log the attendance
                            break
                        else:
                            print("Names do not match. Please try again.")
                            attempts += 1  # Increment attempt counter
                            if attempts < max_attempts:
                                time.sleep(2)  # Wait for 2 seconds before the next attempt
                    finally:
                        GPIO.cleanup()  # Clean up GPIO settings

                if attempts == max_attempts:  # Check if maximum attempts reached
                    print("Attendance not given: Maximum attempts reached.")

        names.append(name)  # Append the recognized name to the list

    for ((top, right, bottom, left), name) in zip(boxes, names):  # Loop over face locations and recognized names
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 225), 2)  # Draw a rectangle around the face
        y = top - 15 if top - 15 > 15 else top + 15  # Set the position for the name label
        cv2.putText(frame, name, (left, y), cv2.FONT_HERSHEY_SIMPLEX, .8, (0, 255, 255), 2)  # Draw the name label

    cv2.imshow("Facial Recognition is Running", frame)  # Display the video frame
    key = cv2.waitKey(1) & 0xFF  # Capture key press

    if key == ord("q"):  # Exit the loop if 'q' is pressed
        break

    fps += 1  # Increment the FPS counter

# Calculate elapsed time and approximate FPS
elapsed_time = time.time() - start_time
print("[INFO] elapsed time: {:.2f}".format(elapsed_time))
print("[INFO] approx. FPS: {:.2f}".format(fps / elapsed_time))

# Clean up and release resources
cv2.destroyAllWindows()
vs.release()
