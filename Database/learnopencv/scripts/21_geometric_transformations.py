'''
transformations:-
scaling
rotation
translation

geomtric transformations:-
affine: all parallel lines in the image remain parallel in output
        need 3 points in input img and correspondign location on output img
        cv.getAffineTransform--> 2X3 matrix passed through cv.warpAffine
perspective: straight lines remain straight even after transofrm
             need 4 points in input img and then corresponding output img
             3 should not be collinear
             cv.warpPerspective
             
'''


import cv2
import numpy as np
img = cv2.imread("images/1.jpg")


cv2.imshow("1",img)
cv2.waitKey(0)
cv2.destroyAllWindows()