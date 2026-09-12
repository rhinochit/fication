'''
slow and fast motion video  
'''

import cv2
cap = cv2.VideoCapture("images/1.mp4")

while cap.isOpened():
    rat,frame = cap.read()
    frame = cv2.resize(frame, (500,500))
    if rat == True:
        cv2.imshow("1",frame)
        if cv2.waitKey(5) & 0xff == ord("p"):
            break
    else:
        break
cap.release()
cv2.destroyAllWindows()