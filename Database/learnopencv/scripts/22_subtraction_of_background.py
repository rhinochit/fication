'''
subtraction of bakcground
'''

import cv2
cap = cv2.VideoCapture("images/1.mp4")
sub = cv2.createBackgroundSubtractorMOG2()

while cap.isOpened():
    r,frame = cap.read()    
    if r == True:
        subv = sub.apply(frame) 
        cv2.imshow("frame", subv)
        if cv2.waitKey(10) & 0xff == ord("p"): #here waitke is essentially frames per second
               break   
    else:
        break

cap.release()
cv2.destroyAllWindows()