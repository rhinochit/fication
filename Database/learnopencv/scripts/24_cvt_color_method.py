'''
CVT color method 
'''
import cv2

org = cv2.imread("images/1.jpg")
new = cv2.cvtColor(org,cv2.COLOR_BGR2GRAY)
cv2.imshow("1",new)
cv2.waitKey(0)
cv2.destroyAllWindows()