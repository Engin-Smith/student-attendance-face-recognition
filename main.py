import os
import pickle
from datetime import datetime

import cvzone
import numpy as np
import cv2
import face_recognition
import face_recognition_models
import firebase_admin
from firebase_admin import credentials
from  firebase_admin import db
from firebase_admin import storage

#connect to database
cred = credentials.Certificate("")
firebase_admin.initialize_app(cred,{
    'databaseURL':"",
    'storageBucket': ""
})

bucket = storage.bucket()

# set up webcam
cap = cv2.VideoCapture(0)
# put 1 for multiple camera
# set camera frame
cap.set(3, 640)
cap.set(4, 480)

# graphic setup
imgBackground = cv2.imread('Resources/background.png')

#Importing the mode images into a list
folderModePath = 'Resources/Modes'
modePathList = os.listdir(folderModePath)
imgModeList = []
for path in modePathList:
    imgModeList.append(cv2.imread(os.path.join(folderModePath, path)))
# print(len(imgModeList))

# import the endcoding and extract the encoding
print("Loading Encode File ...")
file = open('EndcodeFile.p', 'rb')
ecodeListKnownWithIds = pickle.load(file)
file.close()
#extract
encodeListKnown, peopleIds = ecodeListKnownWithIds
# print(peopleIds)
print("Loading Encoded")


# mode type for database
modeType = 0
counter = 0
id = -1
poepleImg = []
#that the variable for call

# control video cap
while True:
    success, img = cap.read()

    # d=checking the new face
    imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

    # face detected and compair
    faceCurFrame = face_recognition.face_locations(imgS)
    #compair
    encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)

    #overlay the webcam on the background
    imgBackground[162:162+480,55:55+640] = img # [] in this we have starting point and ending point/ 162:162+480 the height and 162+480 the end point of the height
#55:55+640 the width 55+640 the end point of the width
    # for mode position
    imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType] # [0] for display the first image

    if faceCurFrame:
        # to loop all encoding to compair it match or not
        for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
            matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
            faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)

            # for select the result or the index
            matchIndex = np.argmin(faceDis)
            # print("Match Index", matchIndex)

            if matches[matchIndex]:
                # print("Known Face Detected")
                # print(peopleIds [matchIndex])

                # draw the ratangle for know as detected
                y1, x2, y2, x1 = faceLoc
                y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                box = 55 + x1, 162 + y1, x2 - x1, y2 - y1
                imgBackground = cvzone.cornerRect(imgBackground, box, rt=0)
                id = peopleIds[matchIndex]

                #counter / count the image
                if counter == 0:
                    cvzone.putTextRect(imgBackground, "Loading", (275, 400))
                    # cv2.imshow("Face Attendance", imgBackground)
                    cv2.waitKey(1)
                    counter = 1
                    modeType = 1

            if counter != 0:

                # get the data to display
                if counter == 1:
                    peoplesInfo = db.reference(f'Peoples/{id}').get()
                    print(peoplesInfo)
                    # Get the Image from the storage
                    blob = bucket.get_blob(f'Images/{id}.jpg')
                    array = np.frombuffer(blob.download_as_string(), np.uint8)
                    poepleImg = cv2.imdecode(array, cv2.COLOR_BGRA2BGR)

                    #update data of attendance
                    datetimeObject = datetime.strptime(peoplesInfo['last_attendance_time'], #date and time  also this place can delay to detect attendance again in this format
                                                       "%Y-%m-%d %H:%M:%S")
                    #find the data time
                    secondsElapsed = (datetime.now() - datetimeObject).total_seconds()
                    print(secondsElapsed)
                    if secondsElapsed >15:
                        ref = db.reference(f'Peoples/{id}')
                        peoplesInfo['total_attendance'] += 1
                        ref.child('total_attendance').set(peoplesInfo['total_attendance'])
                        ref.child('last_attendance_time').set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    else:
                        modeType = 3
                        counter = 0
                        imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

                if modeType !=3:

                    if 10 < counter < 20:
                        modeType = 2
                    imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

                    if counter <= 10:
                        # display the result in correct position
                        cv2.putText(imgBackground, str(peoplesInfo['total_attendance']), (861, 125),
                                    cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 1)
                        cv2.putText(imgBackground, str(peoplesInfo['major']), (973, 550),
                                    cv2.FONT_HERSHEY_TRIPLEX, 0.5, (255, 255, 255), 1)
                        cv2.putText(imgBackground, str(id), (1006, 493),
                                    cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
                        cv2.putText(imgBackground, str(peoplesInfo['total_attendance']), (910, 625),
                                    cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)
                        cv2.putText(imgBackground, str(peoplesInfo['year']), (1025, 625),
                                    cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)
                        cv2.putText(imgBackground, str(peoplesInfo['starting_year']), (1125, 625),
                                    cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)

                        #make the text auto center
                        (w, h), _ = cv2.getTextSize(peoplesInfo['name'], cv2.FONT_HERSHEY_COMPLEX, 1, 1)
                        offset = (414 - w) //2 # know the center fisrt know the image size and // with 2
                        cv2.putText(imgBackground, str(peoplesInfo['name']), (808 + offset, 445),
                                    cv2.FONT_HERSHEY_COMPLEX, 1, (50, 50, 50), 1)
                        # disply or overlay image
                        imgBackground[175:175 + 216, 909:909 + 216] = poepleImg

                    counter +=1

                    if counter >= 20:
                        counter = 0
                        modeType = 0
                        peoplesInfo = []
                        poepleImg = []
                        imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]
    else:
        modeType = 0
        counter = 0

    # cv2.imshow('Webcam ', img)
    cv2.imshow('Face Detection & Recognition Attendance ', imgBackground)
    cv2.waitKey(1)

