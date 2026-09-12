'''
draw polygons on image
'''
import cv2
import numpy as np

img = cv2.imread("images/1.jpg")     
img1 = cv2.resize(img,(500,800))

new = cv2.polylines(img = img1, pts = [np.array([[100,400], [150,300], [300,400], [300,600],[100,600]])], isClosed = True, color= (0,255,255), thickness = 4, lineType = 16)

cv2.imshow("frame", new)
cv2.waitKey(0)          
cv2.destroyAllWindows()    