import cv2
import os

# Get the directory where THIS script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Build path from script location
img_path = os.path.join(script_dir, "..", "images", "2.jpg")

img = cv2.imread(img_path)

if img is None:
    print(f"Error: Could not read image at {img_path}")
else:
    cv2.imshow("frame", img)
    cv2.waitKey(10000)
    cv2.destroyAllWindows()
