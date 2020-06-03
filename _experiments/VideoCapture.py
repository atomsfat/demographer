import numpy as np
import cv2

# Video source - can be camera index number given by 'ls /dev/video*
# or can be a video file, e.g. '~/Video.avi'
cap = cv2.VideoCapture(0)

while True:
    # Capture frame-by-frame
    ret, frame = cap.read()

    # Our operations on the frame come here
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Display the resulting frame
    cv2.imshow('frame',gray)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()




    # cv2image = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGBA)
    #     current_image = Image.fromarray(cv2image)
    #     img_tk = ImageTk.PhotoImage(image=current_image)
    #     self.display.config(image=img_tk)  # show the image
    #     self.display.image = img_tk  # anchor imgtk so it does not be deleted by garbage-collector
