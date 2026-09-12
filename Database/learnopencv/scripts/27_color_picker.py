'''
color picker
'''
import numpy as np
import cv2
def frame(x):
    pass
# img = cv2.imread("images/1.jpg")

new = np.zeros((500,500,3),np.uint8)*255
cv2.namedWindow("colour")
cv2.createTrackbar("R","colour",0,255,frame)
cv2.createTrackbar("G","colour",0,255,frame)
cv2.createTrackbar("B","colour",0,255,frame)

while True:
    cv2.imshow("colour",new)
    if cv2.waitKey(1) & 0xff ==ord("p"):
        break
    r = cv2.getTrackbarPos("R","colour")
    g = cv2.getTrackbarPos("G","colour")
    b = cv2.getTrackbarPos("B","colour")
    new[:]=[b,g,r]
cv2.destroyAllWindows()