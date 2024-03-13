import os
import pickle

import cv2
import face_recognition
import firebase_admin
from firebase_admin import credentials
from  firebase_admin import db
from firebase_admin import storage

#connect to database
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred,{
    'databaseURL':"",
    'storageBucket': ""
})


# Importing the Images
folderPath = 'Images'
PathList = os.listdir(folderPath)
print(PathList)  # call the name
imgList = []
peopleIds = []
for path in PathList:
    imgList.append(cv2.imread(os.path.join(folderPath, path)))
    # print(path)
    # # remove extension png call only name
    # print(os.path.splitext(path)[0])
    # use for people name
    peopleIds.append(os.path.splitext(path)[0])

    #for loop data to database
    fileName = f'{folderPath}/{path}'
    # create bucket
    bucket = storage.bucket()
    #blob is sending
    blob = bucket.blob(fileName)
    blob.upload_from_filename(fileName)


print(peopleIds)


# function encoding
def findEncodings(imagesList):
    encodeList = []
    for img in imagesList:
        # convert BGR to RGB cuz library Opencv use BGR but face recognition use RGB
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        # find encoding
        encode = face_recognition.face_encodings(img)[0]
        # to make encode loop
        encodeList.append(encode)

    return encodeList


print('Encoding Started')
# call the function
encodeListKnown = findEncodings(imgList)
ecodeListKnownWithIds = [encodeListKnown, peopleIds]
print('Encode Complated')

file = open("EndcodeFile.p", 'wb')
pickle.dump(ecodeListKnownWithIds, file)
file.close()
print('File Saved')