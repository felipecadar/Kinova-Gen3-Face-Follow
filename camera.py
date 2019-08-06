"""Terminal command:

color: gst-launch-1.0 rtspsrc location=rtsp://192.168.1.10/color latency=30 ! rtph264depay ! avdec_h264 ! autovideosink

depth: gst-launch-1.0 rtspsrc location=rtsp://192.168.1.10/depth latency=30 ! rtpgstdepay ! videoconvert ! autovideosink
"""

import numpy as np
import cv2
import dlib
# from imutils import face_utils
import time


if __name__ == "__main__":
    
    video_capture = cv2.VideoCapture("rtsp://192.168.1.10/color")
    detector = dlib.get_frontal_face_detector()
    FACTOR = 0.3


    while True:
        # Capture frame-by-frame
        ret, frame = video_capture.read()
        start = time.time()

        res = cv2.resize(frame, None, fx=FACTOR, fy=FACTOR)
        gray = cv2.cvtColor(res, cv2.COLOR_BGR2GRAY)
        rects = detector(gray)    
        
        for (i, rect) in enumerate(rects):
            x1 = int(rect.left() / FACTOR)
            y1 = int(rect.top() / FACTOR)
            x2 = int(rect.right() / FACTOR)
            y2 = int(rect.bottom() / FACTOR)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # Display the video output
        cv2.imshow('Video', frame)

        # Quit video by typing Q
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        end = time.time()

        print(chr(27) + "[2J")
        print("FPS: {}\nFaces: {}".format(1/(end - start), len(rects)))


    video_capture.release()
    cv2.destroyAllWindows()

