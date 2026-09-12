'''
Haar Cascade Face Detection

--> haar-cascade is an algorithm that detectsobjects in images, irrespective of location and image
--> not so complex, run in real time
--> can train to detect various objects like cars, bikes, buildings and fruits
--> runs from (x,y) to (x+w,y+h)
'''
import cv2
img = cv2.imread("images/7.jpg")
gry = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

f = cv2.CascadeClassifier(r"C:\Users\RACHIT\Desktop\PROJECTS\learnopencv\venv\Lib\site-packages\cv2\data\haarcascade_frontalface_default.xml")
d = f.detectMultiScale(gry,1.8,2)
for (x,y,w,h) in d:
    cv2.rectangle(img,(x,y),(x+w,y+h),(0,0,255,3))

cv2.imshow("1",img)
cv2.waitKey(0)
cv2.destroyAllWindows()