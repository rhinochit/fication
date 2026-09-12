'''
video capture with camera
'''
import cv2
cap = cv2.VideoCapture(0)

while True:
    r,frame = cap.read()    
    if r == True:
        frame = cv2.resize(frame,(500,500))
        cv2.imshow("frame", frame)
        if cv2.waitKey(25) & 0xff == ord("p"): 
               break   
    else:
        break
cap.release()
cv2.destroyAllWindows()