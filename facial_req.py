import cv2
import face_recognition
import pickle
import time
import csv
from datetime import datetime
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522

# Initialize RFID reader
reader = SimpleMFRC522()

# Initialize 'currentname' to trigger only when a new person is identified
currentname = "unknown"

# Load encodings
encodingsP = "encodings.pickle"
print("[INFO] loading encodings + face detector...")
with open(encodingsP, "rb") as file:
    data = pickle.load(file)

# Initialize the video stream from the webcam and allow the camera sensor to warm up
print("[INFO] starting video stream...")
vs = cv2.VideoCapture(0)
time.sleep(2.0)

if not vs.isOpened():
    print("[ERROR] Unable to access the camera.")
    exit()

# Set camera resolution (optional)
vs.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
vs.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Attendance logging function
def log_attendance(name, rfid_id):
    with open('attendance.csv', mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), name, rfid_id])

# Start the FPS counter
fps = 0
start_time = time.time()

# Loop over frames from the video file stream
while True:
    # Grab the frame from the threaded video stream
    ret, frame = vs.read()
    if not ret:
        print("[ERROR] No frame captured from the video stream.")
        break

    # Resize the frame to 500px (to speed up processing)
    frame = cv2.resize(frame, (500, int(frame.shape[0] * 500 / frame.shape[1])))

    # Detect the face boxes
    boxes = face_recognition.face_locations(frame)
    # Compute the facial embeddings for each face bounding box
    encodings = face_recognition.face_encodings(frame, boxes)
    names = []

    # Loop over the facial embeddings
    for encoding in encodings:
        # Attempt to match each face in the input image to our known encodings
        matches = face_recognition.compare_faces(data["encodings"], encoding)
        name = "Unknown"  # If face is not recognized, then print Unknown

        # Check to see if we have found a match
        if True in matches:
            # Find the indexes of all matched faces then initialize a dictionary to count the total number of times each face was matched
            matchedIdxs = [i for (i, b) in enumerate(matches) if b]
            counts = {}

            # Loop over the matched indexes and maintain a count for each recognized face
            for i in matchedIdxs:
                name = data["names"][i]
                counts[name] = counts.get(name, 0) + 1

            # Determine the recognized face with the largest number of votes (note: in the event of an unlikely tie, Python will select the first entry in the dictionary)
            name = max(counts, key=counts.get)

            # If someone in your dataset is identified, print their name on the screen
            if currentname != name:
                currentname = name
                print(f"Recognized: {currentname}")

                attempts = 0
                max_attempts = 3  # Maximum number of attempts to scan RFID

                while attempts < max_attempts:
                    print("Hold your RFID tag near the reader")
                    try:
                        rfid_id, rfid_text = reader.read()
                        print(f"RFID ID: {rfid_id}, Text: {rfid_text}")

                        if currentname == rfid_text.strip():
                            # Log attendance
                            log_attendance(currentname, rfid_id)
                            break
                        else:
                            print("Names do not match. Please try again.")
                            attempts += 1
                            if attempts < max_attempts:
                                time.sleep(2)  # Delay between attempts
                    finally:
                        GPIO.cleanup()

                if attempts == max_attempts:
                    print("Attendance not given: Maximum attempts reached.")

        # Update the list of names
        names.append(name)

    # Loop over the recognized faces
    for ((top, right, bottom, left), name) in zip(boxes, names):
        # Draw the predicted face name on the image - color is in BGR
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 225), 2)
        y = top - 15 if top - 15 > 15 else top + 15
        cv2.putText(frame, name, (left, y), cv2.FONT_HERSHEY_SIMPLEX, .8, (0, 255, 255), 2)

    # Display the image to our screen
    cv2.imshow("Facial Recognition is Running", frame)
    key = cv2.waitKey(1) & 0xFF

    # Quit when 'q' key is pressed
    if key == ord("q"):
        break

    # Update the FPS counter
    fps += 1

# Stop the timer and display FPS information
elapsed_time = time.time() - start_time
print("[INFO] elapsed time: {:.2f}".format(elapsed_time))
print("[INFO] approx. FPS: {:.2f}".format(fps / elapsed_time))

# Do a bit of cleanup
cv2.destroyAllWindows()
vs.release()
