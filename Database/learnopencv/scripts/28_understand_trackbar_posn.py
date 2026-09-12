'''
imderstand trackbarpos
'''
import numpy as np
import cv2
def frame(x):
    pass
cv2.namedWindow("bar")
new = np.zeros((500,500,3),np.uint8)*255
cv2.createTrackbar("on","bar",0,100,frame)
while True:
    cv2.imshow("bar", new)
    if cv2.waitKey(1) & 0xff == ord("p"):
        break
    var = cv2.getTrackbarPos("on","bar")
    new[:]= [var,0,0]
cv2.destroyAllWindows()