'''
extract image from video frame wise
also change all '\' to '//'
'''

import cv2
cap = cv2.VideoCapture("images/1.mp4")
c = 0
while cap.isOpened():
    r,frame = cap.read()    
    if r == True:
        frame = cv2.resize(frame,(500,500))
        filename = "C://Users//RACHIT//Desktop//learnopencv//images"+str(c)+".png"
        cv2.imwrite(filename,frame)
        cv2.imshow("1",frame)
        c+=1
        if cv2.waitKey(10) & 0xff == ord("p"): 
               break   
    else:
        break

cap.release()
cv2.destroyAllWindows()