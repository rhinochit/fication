'''
video capture
'''
import cv2
cap = cv2.VideoCapture("images/1.mp4")

while cap.isOpened():
    r,frame = cap.read()    
    if r == True:
        cv2.imshow("frame", frame)
        if cv2.waitKey(30) & 0xff == ord("p"): #here waitke is essentially frames per second
               break   
    else:
        break

cap.release()
cv2.destroyAllWindows()