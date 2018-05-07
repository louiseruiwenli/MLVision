import os
import sqlite3 as sql
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash, abort
from flask import Response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from camera import VideoCamera
from werkzeug.security import generate_password_hash, check_password_hash

import time
import math
from random import *
import face_recognition
import cv2



app = Flask(__name__) # create the application instance :)
app.config.from_object(__name__) # load config from this file , flaskr.py

######################Add User With Login System in the Database#############################
def insertUser(username,password):
    con = sql.connect("database.db")
    cur = con.cursor()
    print (username)
    print (password)
    cur.execute("INSERT INTO users (username,password) VALUES (?,?)", (username,password))
    con.commit()
    con.close()

def retrieveUsers():
    con = sql.connect("database.db")
    cur = con.cursor()
    cur.execute("SELECT username, password FROM users")
    users = cur.fetchall()
    con.close()
    return users

def checkUsernameExit(username):
    con = sql.connect("database.db")
    cur = con.cursor()
    cur.execute("SELECT username FROM users WHERE username = '%s'"%str(username))
    users = cur.fetchone()
    print (users)
    if users:
        return True
    else:
        return False

def checkPassword(username, password):
    con = sql.connect("database.db")
    cur = con.cursor()
    cur.execute("SELECT password FROM users WHERE username = '%s'"%str(username))
    correct_password = cur.fetchone()
    print (correct_password[0])
    #if correct_password[0] == password:
    if check_password_hash(correct_password[0],password):
        return True
    else:
        return False


######################################Database setup end#######################################

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'bih.db'),
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'
))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Set up login database config

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'thisissecret'

db = SQLAlchemy(app)
login_manager = LoginManager();
login_manager.init_app(app)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(30),unique = True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))



def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


##############################################MAIN############################################################
@app.route('/')
def show_index():
    return render_template('main.html')


##############################################Login############################################################
@app.route('/login', methods=['GET', 'POST'])
def Username_login():
    error = ""
    if request.method=='POST':
        check_user_exist = checkUsernameExit(request.form['username'])
        
        #if the username exists, go to password page
        if check_user_exist:
            session['username'] = request.form['username']
            return redirect('/login2')
        else:
            error = "Username does not exit"
    return render_template('login_username.html', error=error)

@app.route('/login2', methods=['GET', 'POST'])
def Password_login():
    error = ""
    if request.method=='POST':
        check_password = checkPassword(session['username'], request.form['password'])
        
        #if password matches, go to face recognition page
        if check_password:
            return redirect('/login3')
        else:
            error = "Invalid password."
    return render_template('login_password.html', error=error)

@app.route('/login3', methods=['GET', 'POST'])
def Photourl_login():
    if request.method=='POST':
        return redirect('/profile')
    
    return render_template('login_photo.html')

def loginVideoStream(camera,username):
    
    path = 'photo'
    file_name = '{}.png'.format(username)
    file_path = os.path.join(path, file_name)
    
    #access user's photo and compare faces
    user_image = face_recognition.load_image_file(file_path)
    face_landmarks_list = face_recognition.face_landmarks(user_image)
    user_face_encoding = face_recognition.face_encodings(user_image)[0]
    
    start = 0
    face_locations = []
    face_encodings = []
    face_names = []
    process_this_frame = True
    face_detected = False;
    real_person_varified = False
    start_counter = False
    user_authenticated = False
    
    COUNTER = 0
    TOTAL = 0
    EYE_AR_CONSEC_FRAMES = 3
    EYE_AR_THRESH = 0.2
    
    
    number = randint(1,5)
    
    def eye_aspect_ratio(eye):
        from scipy.spatial import distance as dist
        # compute the euclidean distances between the two sets of
        # vertical eye landmarks (x, y)-coordinates
        A = dist.euclidean(eye[1], eye[5])
        B = dist.euclidean(eye[2], eye[4])
        # compute the euclidean distance between the horizontal
        # eye landmark (x, y)-coordinates
        C = dist.euclidean(eye[0], eye[3])
        # compute the eye aspect ratio
        ear = (A + B) / (2.0 * C)
        # return the eye aspect ratio
        return ear
    
    while True:
        frame = camera.get_frame()
        
        # Resize frame of video to 1/4 size for faster face recognition processing
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        
        # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
        rgb_small_frame = small_frame[:, :, ::-1]
        
        # Only process every other frame of video to save time
        if process_this_frame:
            # Find all the faces and face encodings in the current frame of video
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_landmarks_list = face_recognition.face_landmarks(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
        
        face_names = []
        for face_encoding in face_encodings:
            # See if the face is a match for the known face(s)
            match = face_recognition.compare_faces([user_face_encoding], face_encoding, 0.45)
            name = "Unknown"
            
            if match[0]:
                name = username
                user_authenticated = True
            else:
                user_authenticated = False
            
            face_names.append(name)
        
        if not face_encodings:
            face_detected = False

        
        process_this_frame = not process_this_frame
        
        if face_landmarks_list and face_landmarks_list[0]:
            leftEye = face_landmarks_list[0]['left_eye']
            rightEye = face_landmarks_list[0]['right_eye']
            leftEAR = eye_aspect_ratio(leftEye)
            rightEAR = eye_aspect_ratio(rightEye)
            ear = (leftEAR + rightEAR) / 2.0
            # check to see if the eye aspect ratio is below the blink
            # threshold, and if so, increment the blink frame counter
            if ear < EYE_AR_THRESH:
                COUNTER += 1
            # otherwise, the eye aspect ratio is not below the blink threshold
            else:
                # if the eyes were closed for a sufficient number of
                # then increment the total number of blinks
                if COUNTER >= EYE_AR_CONSEC_FRAMES:
                    TOTAL += 1
                    # reset the eye frame counter
                    COUNTER = 0
    
        # Display the results
        for (top, right, bottom, left), name in zip(face_locations, face_names):
            # Scale back up face locations since the frame we detected in was scaled to 1/4 size
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4
            
            # Draw a box around the face
            cv2.rectangle(frame, (left, top), (right, bottom), (149, 170, 37), 2)
            
            # Draw a label with a name below the face
            cv2.rectangle(frame, (left, bottom), (right, bottom), (149, 170, 37), cv2.FILLED)
            face_detected = True



        font = cv2.FONT_HERSHEY_SIMPLEX
        if face_detected:
            cv2.putText(frame, "Face Detected", (100, 100), font, 1.2, (149, 170, 37), 3)
            
            if not user_authenticated:
                cv2.putText(frame, "Authentication failed.", (100, 150), font, 1.2, (149, 170, 37), 3)
                face_detected = False
            
            elif user_authenticated and not real_person_varified: #not user_authenticated
                cv2.putText(frame, "Authentication succeeded.", (100, 150), font, 1.2, (149, 170, 37), 3)
                cv2.putText(frame, "Now verifing real persion...", (100, 200), font, 1.2, (149, 170, 37), 3)
                cv2.putText(frame, "Blink {} times".format(number), (100, 250), font, 1.2, (149, 170, 37), 3)
                cv2.putText(frame, "Blinks: {}".format(TOTAL), (100, 300),font, 1.2, (149, 170, 37), 3)
            elif user_authenticated and real_person_varified:
                cv2.putText(frame, "Real Person Varified", (100, 150), font, 1.2, (149, 170, 37), 3)
                cv2.putText(frame, "Now press 'Login'", (100, 200), font, 1.2, (149, 170, 37), 3)
                if not start_counter:
                    start = time.time()
                    start_counter = True

        
        else: #not face detected
            user_authenticated = False
            real_person_varified = False
            TOTAL = 0
            start_counter = False
            number = randint(1,5)
        
        #login and exit video stream
        if math.floor(time.time()-start) == 1:
            break

        
        if face_detected and TOTAL == number:
            real_person_varified = True


        ret, jpeg = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpg\r\n\r\n' + jpeg.tobytes() + b'\r\n')


    cv2.destroyAllWindows()

@app.route('/login_video_feed', methods=['GET', 'POST'])
def login_video_feed():
    #get the username just entered
    username = request.args.get('username')
    
    #video stream
    #pass web cam and username as arguments
    response =  Response(loginVideoStream(VideoCamera(),username),
                         mimetype='multipart/x-mixed-replace; boundary=frame')
                         
    return response



##############################################Login End#######################################################


####################################################Registration#########################################
@app.route('/register', methods=['GET', 'POST'])
def Username():
    error = ""
    if request.method=='POST':
        check_user_exist = checkUsernameExit(request.form['username'])
        if check_user_exist:
            error = "Username already exists!"
        else:
            session['username'] = request.form['username']
            return redirect('/register2')
    return render_template('register_username.html', error = error)


@app.route('/register2', methods=['GET', 'POST'])
def Password():
    if request.method=='POST':
        #session['password']=request.form['password']
        session['password'] = generate_password_hash(request.form['password'])
        return redirect('/register3')
    return render_template('register_password.html')

@app.route('/register3', methods=['GET', 'POST'])
def Photourl():
    
    if request.method=='POST':
        insertUser(session['username'], session['password'])

        return redirect('/profile')
    return render_template('register_photo.html')


def registerVideoStream(camera,username):
    user_image = face_recognition.load_image_file("louise.jpg")
    face_landmarks_list = face_recognition.face_landmarks(user_image)
    user_face_encoding = face_recognition.face_encodings(user_image)[0]
    start = 0
    
    face_locations = []
    face_encodings = []
    face_names = []
    process_this_frame = True
    face_detected = False;
    real_person_varified = False
    start_counter = False
    take_photo = False
    
    COUNTER = 0
    TOTAL = 0
    EYE_AR_CONSEC_FRAMES = 3
    EYE_AR_THRESH = 0.2
    
    
    number = randint(1,5)
    
    def eye_aspect_ratio(eye):
        from scipy.spatial import distance as dist
        # compute the euclidean distances between the two sets of
        # vertical eye landmarks (x, y)-coordinates
        A = dist.euclidean(eye[1], eye[5])
        B = dist.euclidean(eye[2], eye[4])
        # compute the euclidean distance between the horizontal
        # eye landmark (x, y)-coordinates
        C = dist.euclidean(eye[0], eye[3])
        # compute the eye aspect ratio
        ear = (A + B) / (2.0 * C)
        # return the eye aspect ratio
        return ear
    
    while True:
        frame = camera.get_frame()
        
        # Resize frame of video to 1/4 size for faster face recognition processing
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        
        # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
        rgb_small_frame = small_frame[:, :, ::-1]
        
        # Only process every other frame of video to save time
        if process_this_frame:
            # Find all the faces and face encodings in the current frame of video
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_landmarks_list = face_recognition.face_landmarks(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
        
        face_names = []
        for face_encoding in face_encodings:
            # See if the face is a match for the known face(s)
            match = face_recognition.compare_faces([user_face_encoding], face_encoding)
            name = "Unknown"
            
            if match[0]:
                name = "Louise"
            
            face_names.append(name)

        if not face_encodings:
            face_detected = False
            #session['face_detected'] = False
        
        process_this_frame = not process_this_frame
        
        if face_landmarks_list and face_landmarks_list[0]:
            leftEye = face_landmarks_list[0]['left_eye']
            rightEye = face_landmarks_list[0]['right_eye']
            leftEAR = eye_aspect_ratio(leftEye)
            rightEAR = eye_aspect_ratio(rightEye)
            ear = (leftEAR + rightEAR) / 2.0
            # check to see if the eye aspect ratio is below the blink
            # threshold, and if so, increment the blink frame counter
            if ear < EYE_AR_THRESH:
                COUNTER += 1
            # otherwise, the eye aspect ratio is not below the blink threshold
            else:
                # if the eyes were closed for a sufficient number of
                # then increment the total number of blinks
                if COUNTER >= EYE_AR_CONSEC_FRAMES:
                    TOTAL += 1
                    # reset the eye frame counter
                    COUNTER = 0
    
        # Display the results
        for (top, right, bottom, left), name in zip(face_locations, face_names):
            # Scale back up face locations since the frame we detected in was scaled to 1/4 size
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4
            
            # Draw a box around the face
            cv2.rectangle(frame, (left, top), (right, bottom), (149, 170, 37), 2)
            
            # Draw a label with a name below the face
            cv2.rectangle(frame, (left, bottom), (right, bottom), (149, 170, 37), cv2.FILLED)
            face_detected = True
  


        font = cv2.FONT_HERSHEY_SIMPLEX
        if face_detected and not real_person_varified:
            cv2.putText(frame, "Face Detected", (100, 100), font, 1.2, (149, 170, 37), 3)
            cv2.putText(frame, "Now Varifying Real Person...", (100, 150), font, 1.2, (149, 170, 37), 3)
            cv2.putText(frame, "Blink {} times".format(number), (100, 200), font, 1.2, (149, 170, 37), 3)
            cv2.putText(frame, "Blinks: {}".format(TOTAL), (100, 250),font, 1.2, (149, 170, 37), 3)
            #cv2.putText(frame, "EAR: {:.2f}".format(ear), (300, 30),font, 0.7, (0, 0, 255), 3)
        elif face_detected and real_person_varified:
            cv2.putText(frame, "Real Person Varified", (100, 100), font, 1.2, (149, 170, 37), 3)
            cv2.putText(frame, "Your photo will be taken in 5 seconds", (100, 150), font, 1.2, (149, 170, 37), 3)
            if not start_counter:
                start = time.time()
                start_counter = True
        elif not face_detected:
            real_person_varified = False
            take_photo = False
            TOTAL = 0
            start_counter = False
            number = randint(1,5)

        #photo taking count down
        if math.floor(time.time()-start) == 1:
            cv2.putText(frame, "5", (100, 200), font, 1.0, (149, 170, 37), 7)

        if math.floor(time.time()-start) == 2:
            cv2.putText(frame, "4", (100, 200), font, 1.0, (149, 170, 37), 7)

        if math.floor(time.time()-start) == 3:
            cv2.putText(frame, "3", (100, 200), font, 1.0, (149, 170, 37), 7)

        if math.floor(time.time()-start) == 4:
            cv2.putText(frame, "2", (100, 200), font, 1.0, (149, 170, 37), 7)
        
        
        if math.floor(time.time()-start) == 5:
            cv2.putText(frame, "1", (100, 200), font, 1.0, (149, 170, 37), 7)

        if math.floor(time.time()-start) == 6:
            #save the current frame as png file
            if not take_photo:
                path = 'photo'
                print("Username: {}".format(username))
                file_name = '{}.png'.format(username)
                cv2.imwrite(os.path.join(path, file_name),frame)
                take_photo = True
            
        
        if math.floor(time.time()-start) == 7:
            cv2.putText(frame, "Photo taken! Now press 'Login'", (100, 200), font, 1.0,(149, 170, 37), 5)

        if math.floor(time.time()-start) == 8:
            break

        if face_detected and TOTAL == number:
            real_person_varified = True

        
        ret, jpeg = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpg\r\n\r\n' + jpeg.tobytes() + b'\r\n')

    cv2.destroyAllWindows()


@app.route('/register_video_feed', methods=['GET', 'POST'])
def register_video_feed():
    #get the username just entered
    username = request.args.get('username')

    #video stream
    #pass web cam and username as arguments
    response =  Response(registerVideoStream(VideoCamera(),username),
                         mimetype='multipart/x-mixed-replace; boundary=frame')

    return response



####################################################Registration End#########################################

@app.route('/profile')
def profile():
    return render_template('profile.html', user=session['username'])

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)
