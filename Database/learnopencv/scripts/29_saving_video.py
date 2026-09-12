'''
saving video 

Line 1: Sets the video codec (compression format)

python
f = cv2.VideoWriter_fourcc(*"XVID")
VideoWriter_fourcc = picks a video compression format
*"XVID" = XVID is a common video format (the * unpacks the string)
f = stores this codec choice

Line 2: Creates a video writer object (saves video to file)

python
out = cv2.VideoWriter("demo.mp4", f, 40.0, (640,480))
"demo.mp4" = output filename
f = use the XVID codec from above
40.0 = frames per second (FPS)
(640,480) = video resolution (width, height)
'''
import cv2
import numpy as np

cap = cv2.VideoCapture(0)
f = cv2.VideoWriter_fourcc(*"mp4v")
out = cv2.VideoWriter("demo.mp4",f,30.0,(640,480))

while True:
    r,frame = cap.read()    
    if r == True:
        frame = cv2.flip(frame,1)
        out.write(frame)
        cv2.imshow("frame",frame)
        if cv2.waitKey(25) & 0xff == ord("p"): 
               break   
    else:
        break
out.release()
cap.release()
cv2.destroyAllWindows()