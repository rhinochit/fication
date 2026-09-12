'''
get filename
'''
import cv2
import numpy as np
import os

listname = os.listdir("images")
print(listname)

for name in listname:
    path = "images"
    img_name = path + "\\" + name
    img = cv2.imread(img_name)
    img = cv2.resize(img,(500,600))
    cv2.imshow("me", img)
    cv2.waitKey(1000)
cv2.destroyAllWindows()