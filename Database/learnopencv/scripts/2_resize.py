'''
resize image
'''
import cv2

img = cv2.imread("images/2.jpg")     
 
img1 = cv2.resize(img,(500,800))
cv2.imshow("frame", img1)

cv2.waitKey(0)          
cv2.destroyAllWindows()    

