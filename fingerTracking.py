import cv2
import mediapipe as mp
import numpy as np
import time, os

import flexbuffers
import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):
    if rc==0:
        print('Connected OK')
    else:
        print('Bad connection Returned code = ',rc)

def on_disconnect(client, userdata, flags, rc=0):
    print(str(rc))

def on_publish(client, userdata, mid):
    print('In on_pub callback mid = ',mid)

client = mqtt.Client()
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_publish = on_publish
client.connect('192.168.75.85', 1883)
client.loop_start()

# MediaPipe hands model
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(
    max_num_hands=2,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5)

cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, img = cap.read()

    img = cv2.flip(img, 1)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    result = hands.process(img)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    if result.multi_hand_landmarks is not None:
        finger_elements = {
            "hand" : "right",
            "fin0" : "0",
            "fin1" : "0",
            "fin2" : "0"
        }
        finger_data = finger_elements.items()

        count = 0
        for res in result.multi_hand_landmarks:
            joint = np.zeros((21, 4))
            for j, lm in enumerate(res.landmark):
                joint[j] = [lm.x, lm.y, lm.z, lm.visibility]

            mp_drawing.draw_landmarks(img, res, mp_hands.HAND_CONNECTIONS)

            if count==0:
                finger_elements["hand"]="right"
            elif count==1:
                finger_elements["hand"]="left"

            for i in range(0,5):
                index = "fin"+str(i)
                element = ""
                for j in range(0,3):
                    element += str(joint[(i+1)*4][j])+','
                element = element[:-1]
                finger_elements[index] = element

            print(finger_elements)

            fbb = flexbuffers.Builder()
            fbb.MapFromElements(finger_elements)
            data = fbb.Finish()
            client.publish("/finger",data,1)

            count+=1

        cv2.putText(img, f'Tracking {len(result.multi_hand_landmarks)} hands ...', org=(10, 30), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=1, color=(255, 255, 255), thickness=2)

    cv2.imshow('img', img)

    if cv2.waitKey(1) == ord('q'):
        break
