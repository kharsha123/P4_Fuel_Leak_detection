import numpy as np
import cv2
from config import *
from datetime import datetime

class Detection:
    def __init__(self):
        self.project_name = 'object detection using Yolo_V8'
        self.present_classes = ['Present', 'Piston']  # 'Present' and 'Piston' are considered present

    def Detect_V8(self, frame, model):
        """
        Perform object detection using YOLOv8 model, including segmentation.

        Args:
            frame (numpy.ndarray): Input image frame.
            model: YOLOv8 model.

        Returns:
            tuple: A tuple containing output list, bounding boxes, confidences, and annotated frame.
        """
        # cv2.imwrite("Capture//" + datetime.now().strftime("%d_%m_%Y_%H_%M_%S") + ".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 100])

        try:
            excep = ['Absent']  # 'Absent' class to be shown in red
            results = model(frame, conf=0.7, device='cpu', imgsz=640, verbose=False)  # list of Results objects
            no = 0
            bbox = []
            output_list = []

            for result in results:
                no += 1
                boxes = result.boxes  # Boxes object for bbox outputs
                names = result.names
                conf = [str(x) for x in np.array(boxes.conf)]
                cls = [str(x) for x in np.array(boxes.cls)]
                output_list = [names[int(key)] for key in [str(int(float(elem))) for elem in cls]]

                for id, box in enumerate(np.array(boxes.xyxy)):
                    x, y, x2, y2 = round(box[0]), round(box[1]), round(box[2]), round(box[3])
                    bbox.append([box[0], box[1], box[2], box[3]])

                    # Determine color based on the object detected
                    if output_list[id] in self.present_classes:
                        color = (0, 255, 0)  # Green color for 'Present' and 'Piston'
                    elif output_list[id] in excep:
                        color = (0, 0, 255)  # Red color for 'Absent'

                    # Draw bounding box and label
                    cv2.rectangle(frame, (x, y), (x2, y2), color, 2)
                    cv2.putText(frame, output_list[id], (x - 10, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 3)
                    cv2.putText(frame, str(round(float(conf[id]), 2)), (x - 30, y - 40), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 3)

                    # If masks are available (segmentation), draw the shaded region
                    if result.masks is not None and len(result.masks) > 0:
                        mask = result.masks[id].cpu().numpy()
                        mask = mask.astype(np.uint8) * 255  # Convert to binary mask (0 or 255)
                        
                        # Use cv2 to find contours and fill the segmented area
                        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                        for contour in contours:
                            cv2.fillPoly(frame, [contour], color=(0, 255, 0, 100))  # Green with some transparency

            return output_list, bbox, conf, frame

        except Exception as ee:
            print('Issue in detection ', str(ee))

# Create an instance of the Detection class
obj_detection = Detection()
