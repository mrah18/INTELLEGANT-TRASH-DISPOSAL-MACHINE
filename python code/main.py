
#dependencies: ultralytics, opencv-python, pyserial

import cv2
import serial
import time
from ultralytics import YOLO

COM_PORT = 'COM9'
BAUD_RATE = 115200
CONFIDENCE_THRESHOLD = 0.80

# Attempt to connect to ESP32 
try:
    esp32 = serial.Serial(port=COM_PORT, baudrate=BAUD_RATE, timeout=1)
    time.sleep(2)  
    print(f"Successfully connected to ESP32 on {COM_PORT}")
except serial.SerialException:
    print(f"Error: Could not open port {COM_PORT}. Make sure the Serial Monitor is closed.")
    exit()
# Place the model file in the same directory as this script

model = YOLO(r"EyeOfCat.pt")
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open webcam.")
    esp32.close()
    exit()

required_hold_time = 1.5  
sorting_cooldown = 5.0  

current_target = None
detect_start_time = 0
last_sort_time = 0

print("\nAI Sorting Started. Press 'q' in the video window to quit.")

while True:
    success, frame = cap.read()
    if not success:
        print("Failed to grab frame.")
        break

  
    results = model(frame, verbose=False)

    for class_id, class_name in results[0].names.items():
        if class_name.strip().lower() == "cup":
            results[0].names[class_id] = "paper"

    current_time = time.time()
    time_since_last_sort = current_time - last_sort_time

    
    if time_since_last_sort > sorting_cooldown:
        boxes = results[0].boxes
        if len(boxes) > 0:
            detected_id = int(boxes.cls[0])
            confidence = boxes.conf[0].item()
            detected_name = results[0].names[detected_id].strip().lower()

           
            if confidence >= CONFIDENCE_THRESHOLD:
                if detected_name != current_target:
                    current_target = detected_name
                    detect_start_time = current_time
                    
                elif (current_time - detect_start_time) >= required_hold_time:
                    cmd = None
                    if detected_name == "plastic":
                        cmd = 'P'
                    elif detected_name == "paper": 
                        cmd = 'C'

                    if cmd:
                        esp32.write(cmd.encode())
                        print(f"CONFIRMED: {detected_name.upper()} ({confidence:.2f}). Sent '{cmd}'.")
                        
                        last_sort_time = current_time
                        time_since_last_sort = 0 
                        current_target = None 
            else:
                # This else belongs to the confidence check
                current_target = None
        else:
            # This else belongs to the len(boxes) > 0 check
            current_target = None
    
    annotated_frame = results[0].plot()

   
    if time_since_last_sort <= sorting_cooldown:
        time_left = round(sorting_cooldown - time_since_last_sort, 1)
        cv2.putText(annotated_frame, f"SORTING... Please wait {time_left}s", (20, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)

    cv2.imshow("Live Custom YOLOv11", annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break


cap.release()
cv2.destroyAllWindows()
if 'esp32' in locals() and esp32.is_open:
    esp32.close()
    print("Serial connection closed.")
