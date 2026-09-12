'''
detecting faces and their smiles
'''
import cv2
img = cv2.imread("images/8.jpg")

cv2.imshow("frame", img)
cv2.waitKey(0)
cv2.destroyAllWindows()