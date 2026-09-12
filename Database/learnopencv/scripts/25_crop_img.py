'''
crop images
'''

import cv2
img = cv2.imread("images/1.jpg")
crop = img[200:500,100:400]
cv2.imshow("1",crop)
cv2.waitKey(0)
cv2.destroyAllWindows()