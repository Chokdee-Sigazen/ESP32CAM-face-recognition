from flask import Flask, request, jsonify
import os
from datetime import datetime
import cv2
import numpy as np
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from threading import Thread
import time

app = Flask(__name__)

# Setup Google Sheets
scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
client = gspread.authorize(creds)

# Open the Google Sheet
sheet = client.open('Employee_Attendance').sheet1

# Create necessary directories
if not os.path.exists('known_faces'):
    os.makedirs('known_faces')
if not os.path.exists('uploads'):
    os.makedirs('uploads')

def train_face(name):
    """Train the system with photos of a person"""
    try:
        # Create person directory if it doesn't exist
        person_dir = f"known_faces/{name}"
        if not os.path.exists(person_dir):
            os.makedirs(person_dir)
        
        # Count existing photos
        existing_photos = len([f for f in os.listdir(person_dir) if f.endswith('.jpg')])
        
        # Get the latest photo file
        photos = [f for f in os.listdir('.') if f.startswith('photo_') and f.endswith('.jpg')]
        if not photos:
            print("No photos found")
            return None
            
        latest_photo = max(photos, key=os.path.getctime)
        print(f"Processing photo: {latest_photo}")
        
        # Load and verify image
        image = cv2.imread(latest_photo)
        if image is None:
            print("Failed to load image")
            return None
            
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detect face in the image
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        
        if len(faces) == 0:
            print("No face detected in training image")
            return None
            
        # Use the first detected face
        (x, y, w, h) = faces[0]
        face_img = gray[y:y+h, x:x+w]
        
        # Save as next number in sequence
        face_path = f"{person_dir}/face_{existing_photos + 1}.jpg"
        success = cv2.imwrite(face_path, face_img)
        
        if success:
            print(f"Face #{existing_photos + 1} saved for {name} at {face_path}")
            return face_path
        else:
            print("Failed to save face image")
            return None
            
    except Exception as e:
        print(f"Error in train_face: {e}")
        return None

def recognize_face(face_image, known_faces_dir='known_faces'):
    """Compare a face against all known faces"""
    try:
        face_gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
        
        best_match = None
        lowest_diff = float('inf')
        
        print(f"Looking for faces in {known_faces_dir}")
        
        # Go through each person's directory
        for person in os.listdir(known_faces_dir):
            person_dir = os.path.join(known_faces_dir, person)
            if not os.path.isdir(person_dir):
                continue
                
            print(f"Checking person: {person}")
            
            # Compare with each photo of this person
            person_diffs = []
            for face_file in os.listdir(person_dir):
                if face_file.endswith('.jpg'):
                    known_face_path = os.path.join(person_dir, face_file)
                    print(f"Comparing with {face_file}")
                    
                    known_face = cv2.imread(known_face_path, cv2.IMREAD_GRAYSCALE)
                    if known_face is None:
                        print(f"Could not read {face_file}")
                        continue
                    
                    # Resize to match
                    try:
                        if known_face.shape != face_gray.shape:
                            known_face = cv2.resize(known_face, (face_gray.shape[1], face_gray.shape[0]))
                    except Exception as e:
                        print(f"Error resizing: {e}")
                        continue
                    
                    # Compare images
                    try:
                        diff = cv2.matchTemplate(face_gray, known_face, cv2.TM_SQDIFF_NORMED)[0][0]
                        person_diffs.append(diff)
                        print(f"Difference score: {diff}")
                    except Exception as e:
                        print(f"Error comparing: {e}")
                        continue
            
            # Use average of top 3 best matches
            if person_diffs:
                person_diffs.sort()
                avg_diff = sum(person_diffs[:min(3, len(person_diffs))]) / min(3, len(person_diffs))
                print(f"Average difference for {person}: {avg_diff}")
                
                if avg_diff < lowest_diff:
                    lowest_diff = avg_diff
                    best_match = person
        
        print(f"Best match: {best_match} with difference: {lowest_diff}")
        
        # Return match if confidence is high enough
        if lowest_diff < 0.7:  # Adjust this threshold as needed
            return best_match
        return "Unknown"
        
    except Exception as e:
        print(f"Error in recognize_face: {e}")
        return "Unknown"

def process_image_for_faces(image_path):
    """Process image and detect faces"""
    # Read the image
    image = cv2.imread(image_path)
    if image is None:
        print("Error: Could not read image")
        return 0, None, "Unknown"
    
    image = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
    # Image preprocessing
    print("Original image size:", image.shape)
    
    # Convert to grayscale and enhance
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)  # Enhance contrast
    gray = cv2.GaussianBlur(gray, (5, 5), 0)  # Reduce noise
    
    # Try multiple cascade classifiers
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    alt_face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_alt.xml')
    
    # First attempt with default cascade
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.2,
        minNeighbors=3,
        minSize=(20, 20),
        flags=cv2.CASCADE_SCALE_IMAGE
    )
    
    # If no faces found, try alternate cascade
    if len(faces) == 0:
        print("No faces found with default cascade, trying alternate...")
        faces = alt_face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.3,
            minNeighbors=3,
            minSize=(30, 30)
        )
    
    print(f"Number of faces detected: {len(faces)}")
    recognized_name = "Unknown"
    
    # Process each face
    for (x, y, w, h) in faces:
        # Extract face region with margin
        margin = 20
        x1 = max(x - margin, 0)
        y1 = max(y - margin, 0)
        x2 = min(x + w + margin, image.shape[1])
        y2 = min(y + h + margin, image.shape[0])
        face_img = image[y1:y2, x1:x2]
        
        print("Attempting to recognize face...")
        
        # Recognize face
        name = recognize_face(face_img)
        print(f"Recognition result: {name}")
        
        # Update recognized name if not Unknown
        if name != "Unknown":
            recognized_name = name
        
        # Draw rectangle and name
        cv2.rectangle(image, (x, y), (x+w, y+h), (0, 255, 0), 2)
        
        # Put text with background for better visibility
        text_size = cv2.getTextSize(name, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)[0]
        cv2.rectangle(image, (x, y - text_size[1] - 10), (x + text_size[0], y), (0, 255, 0), cv2.FILLED)
        cv2.putText(image, name, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 2)
    
    # Save debug images
    cv2.imwrite("debug_gray.jpg", gray)
    output_path = f"detected_{image_path}"
    cv2.imwrite(output_path, image)
    
    # Return results
    if len(faces) > 0:
        print(f"Successfully processed image. Found {len(faces)} faces. Name: {recognized_name}")
    else:
        print("No faces detected in the image")
    
    return len(faces), output_path, recognized_name

def record_attendance(employee_name="Unknown"):
    """Record attendance in Google Sheets"""
    try:
        # Get the Employees worksheet
        if employee_name == "Unknown":
            return
        employees_sheet = client.open('Employee_Attendance').worksheet('Employees')
        
        # Find the employee in the Employees sheet
        # Search in the Name column
        cell = employees_sheet.find(employee_name)
        
        if cell:
            # Update Status to "Yes"
            employees_sheet.update_cell(cell.row, 4, "Yes")  # Column 4 is Status
            
            # Record in Attendance sheet
            attendance_sheet = client.open('Employee_Attendance').worksheet('Attendance')
            now = datetime.now()
            date = now.strftime('%Y-%m-%d')
            time = now.strftime('%H:%M:%S')
            
            # Get employee ID from Employees sheet
            employee_id = employees_sheet.cell(cell.row, 1).value  # Column 1 is Employee ID
            
            # Record in Attendance sheet
            attendance_sheet.append_row([date, time, employee_id, employee_name])
            
            print(f"Recorded attendance for {employee_name} (ID: {employee_id})")
            print(f"Updated status to Yes")
            return True
        else:
            print(f"Employee {employee_name} not found in database")
            return False
            
    except Exception as e:
        print(f"Error recording attendance: {e}")
        return False

@app.route('/upload', methods=['POST'])
def upload_photo():
    """Handle photo uploads from ESP32-CAM"""
    try:
        filename = f"photo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        filepath = os.path.join('uploads', filename)
        
        with open(filepath, 'wb') as f:
            f.write(request.get_data())
        
        num_faces, processed_path, recognized_name = process_image_for_faces(filepath)
        if num_faces > 0:
            # Record attendance with the recognized name
            record_attendance(recognized_name)
            return f'{recognized_name}'
        else:
            return jsonify({
                'status': 'not found face',
                'message': 'No faces detected Please try again'
            }), 201
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/')
def dashboard():
    try:
        # Get employee data
        employees_sheet = client.open('Employee_Attendance').worksheet('Employees')
        employees = employees_sheet.get_all_records()
        
        # Get attendance data
        attendance_sheet = client.open('Employee_Attendance').worksheet('Attendance')
        attendance = attendance_sheet.get_all_records()
        
        # Get today's date
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Filter today's attendance
        today_attendance = [record for record in attendance if record['Date'] == today]
        
        # Calculate statistics
        total_employees = len(employees)
        present_today = len(set([record['Employee ID'] for record in today_attendance]))
        absent_today = total_employees - present_today
        
        return render_template('dashboard.html',
                             employees=employees,
                             today_attendance=today_attendance,
                             total_employees=total_employees,
                             present_today=present_today,
                             absent_today=absent_today,
                             today_date=today)
    except Exception as e:
        return f"Error: {str(e)}"


def add_new_photos():
    """Add multiple photos of a person"""
    name = input("Enter the person's name: ")
    num_photos = int(input("How many photos do you want to take? "))
    
    print(f"\nWill take {num_photos} photos of {name}")
    print("Press Enter before each photo to continue...")
    
    for i in range(num_photos):
        input(f"\nPress Enter to take photo {i+1}/{num_photos}...")
        saved_path = train_face(name)
        if saved_path:
            print(f"Saved as {saved_path}")
        else:
            print("Failed to save photo")
    
    print(f"\nFinished adding photos for {name}")

def list_database():
    """List all people in the database"""
    print("\nCurrent Database Contents:")
    print("--------------------------")
    for person in os.listdir('known_faces'):
        person_dir = os.path.join('known_faces', person)
        if os.path.isdir(person_dir):
            num_photos = len([f for f in os.listdir(person_dir) if f.endswith('.jpg')])
            print(f"{person}: {num_photos} photos")

if __name__ == '__main__':
    # Start Flask server in a separate thread
    server = Thread(target=lambda: app.run(host='0.0.0.0', port=8080, debug=False))
    server.daemon = True
    server.start()
    
    while True:
        print("\nESP32-CAM Face Recognition System")
        print("1. Process latest photo")
        print("2. Add new person to database")
        print("3. List database contents")
        print("4. View Today's Attendance")
        print("5. Exit")
        
        choice = input("Enter your choice (1-5): ")
        
        if choice == '1':
            photos = [f for f in os.listdir('.') if f.startswith('photo_') and f.endswith('.jpg')]
            if photos:
                latest_photo = max(photos, key=os.path.getctime)
                num_faces, processed_path = process_image_for_faces(latest_photo)
                print(f"Found {num_faces} faces in the image")
                print(f"Processed image saved as {processed_path}")
            else:
                print("No photos found")
                
        elif choice == '2':
            add_new_photos()
            
        elif choice == '3':
            list_database()
            
        elif choice == '4':
            try:
                records = sheet.get_all_records()
                today = datetime.now().strftime('%Y-%m-%d')
                today_records = [r for r in records if r['Date'] == today]
                
                print("\nToday's Attendance:")
                print("-" * 50)
                for record in today_records:
                    print(f"Time: {record['Time']}")
                    print(f"Name: {record['Employee Name']}")
                    print(f"Status: {record['Status']}")
                    print("-" * 50)
            except Exception as e:
                print(f"Error fetching attendance: {e}")
                
        elif choice == '5':
            print("Exiting...")
            break
            
        else:
            print("Invalid choice. Please try again.")