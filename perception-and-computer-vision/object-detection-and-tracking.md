---
icon: chart-scatter-3d
---

# Object Detection and Tracking

### Object Detection and Tracking with YOLO <a href="#object-detection-and-tracking-with-yolo" id="object-detection-and-tracking-with-yolo"></a>

<figure><img src="../.gitbook/assets/images (5).jpg" alt=""><figcaption></figcaption></figure>

Object detection and tracking are fundamental capabilities in computer vision and robotics, enabling systems to identify, locate, and follow objects of interest within images or video streams. YOLO (You Only Look Once) is a state-of-the-art, real-time object detection system known for its speed and accuracy. This page explores how to perform object detection and extend it to tracking using YOLO, particularly with the user-friendly Ultralytics YOLO framework.

### 1. Understanding Object Detection with YOLO

**What is Object Detection?**\
Object detection is the process of identifying and locating one or more objects within an image or video. It involves drawing bounding boxes around detected objects and assigning class labels (e.g., "car," "person," "dog") to them [5](https://encord.com/blog/yolo-object-detection-guide/).

**What is YOLO?**\
YOLO (You Only Look Once) is a revolutionary object detection algorithm that processes images in a single pass, making it exceptionally fast and suitable for real-time applications [5](https://encord.com/blog/yolo-object-detection-guide/), [7](https://neptune.ai/blog/object-detection-with-yolo-hands-on-tutorial). Unlike traditional methods that perform detection in multiple stages, YOLO views object detection as a single regression problem, directly predicting bounding box coordinates and class probabilities from full images [5](https://encord.com/blog/yolo-object-detection-guide/).

**How YOLO Works (High-Level Overview):**

<figure><img src="../.gitbook/assets/0_OsG7n0U3jMQEuv9k.gif" alt=""><figcaption></figcaption></figure>

1. **Grid Creation:** YOLO divides the input image into an S x S grid of cells [2](https://github.com/yash42828/YOLO-object-detection-with-OpenCV), [5](https://encord.com/blog/yolo-object-detection-guide/).
2. **Bounding Box Prediction:** Each grid cell is responsible for detecting objects whose centers fall within that cell. Each cell predicts 'B' bounding boxes and a confidence score for each box. The confidence score reflects how certain the model is that the box contains an object and how accurate it believes the bounding box is [5](https://encord.com/blog/yolo-object-detection-guide/), [7](https://neptune.ai/blog/object-detection-with-yolo-hands-on-tutorial).
3. **Class Probability Prediction:** Independently, each grid cell also predicts 'C' conditional class probabilities-the probability that a detected object belongs to a particular class (e.g., car, person, dog), assuming an object is present [5](https://encord.com/blog/yolo-object-detection-guide/), [7](https://neptune.ai/blog/object-detection-with-yolo-hands-on-tutorial).
4. **Non-Max Suppression (NMS):** YOLO's initial output often includes multiple bounding boxes for the same object. NMS is a post-processing step that filters these detections, discarding boxes with lower confidence scores and high overlap (Intersection over Union - IoU) with higher-confidence boxes, thus retaining only the most accurate bounding box for each detected object [5](https://encord.com/blog/yolo-object-detection-guide/), [7](https://neptune.ai/blog/object-detection-with-yolo-hands-on-tutorial).

YOLO models are often pre-trained on large datasets like COCO (Common Objects in Context), which contains 80 object classes commonly found in everyday scenes [2](https://github.com/yash42828/YOLO-object-detection-with-OpenCV), [4](https://core-electronics.com.au/guides/yolo-object-detection-on-the-raspberry-pi-ai-hat-writing-custom-python/).

### 2. DIY Object Detection with Ultralytics YOLO

Ultralytics YOLO (e.g., YOLOv8) provides a very accessible Python API for performing object detection with pre-trained models or custom-trained models [1](https://docs.ultralytics.com/modes/track/), [6](https://pyimagesearch.com/2024/06/17/object-tracking-with-yolov8-and-python/).

**Steps & Code Snippet:**

1.  **Installation:**\
    First, install the Ultralytics library.

    ```
    bashpip install ultralytics
    ```
2.  **Perform Detection:**\
    Create a Python script to load a pre-trained YOLO model and run detection on an image.

    ```
    pythonfrom ultralytics import YOLO
    from PIL import Image
    import cv2 # OpenCV for displaying

    # Load a pre-trained YOLOv8n model (n for nano, a small and fast version)
    model = YOLO("yolov8n.pt")

    # Define the path to your image
    image_path = 'path_to_your_image.jpg' # Replace with your image path

    # Perform object detection
    results = model(image_path)

    # Process results
    # results is a list of Results objects.
    for r in results:
        # Each 'r' is a Results object for a single image.
        # r.show()  # Display the image with detections (opens a new window)
        # r.save(filename='result.jpg') # Save the image with detections

        # To manually access and draw bounding boxes using OpenCV:
        img = cv2.imread(image_path)
        for box in r.boxes:
            # Bounding box coordinates
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            # Confidence score
            confidence = box.conf[0]
            # Class ID
            class_id = int(box.cls[0])
            # Get class name from model
            class_name = model.names[class_id]

            # Draw bounding box and label
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            label = f"{class_name}: {confidence:.2f}"
            cv2.putText(img, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Display the image with OpenCV
        cv2.imshow("YOLOv8 Detection", img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    ```

    _(Ensure you have an image file at `path_to_your_image.jpg` or update the path)_

### 3. Understanding Object Tracking

<figure><img src="../.gitbook/assets/images (6).jpg" alt=""><figcaption></figcaption></figure>

**What is Object Tracking?**\
Object tracking extends object detection by not only identifying objects but also assigning and maintaining a unique ID for each detected object as it moves across frames in a video. This allows the system to follow individual objects over time [1](https://docs.ultralytics.com/modes/track/), [6](https://pyimagesearch.com/2024/06/17/object-tracking-with-yolov8-and-python/).

**Why is it Useful?**\
Tracking is critical for applications like surveillance (monitoring individuals), traffic analysis (vehicle movement), sports analytics (player tracking), and robotics (following targets) [1](https://docs.ultralytics.com/modes/track/).

Ultralytics YOLO supports multiple tracking algorithms out-of-the-box, making it easy to implement robust object tracking [1](https://docs.ultralytics.com/modes/track/).

### 4. DIY Object Tracking with Ultralytics YOLO

Ultralytics YOLO provides a simple `track()` method for performing multi-object tracking on video streams.

**Steps & Code Snippet:**

1.  **Installation:** (If not already done)

    ```
    bashpip install ultralytics
    ```
2.  **Perform Tracking on a Video:**\
    Create a Python script to load a YOLO model and track objects in a video.

    ```
    pythonfrom ultralytics import YOLO
    import cv2

    # Load a pre-trained YOLOv8n model
    model = YOLO("yolov8n.pt")

    # Define the path to your video file or use 0 for webcam
    video_path = 'path_to_your_video.mp4' # Replace with your video path or 0 for webcam
    # For webcam: cap = cv2.VideoCapture(0)

    # Perform object tracking on the video source
    # The 'tracker' argument specifies the tracking algorithm.
    # BoT-SORT and ByteTrack are common choices. Default is BoT-SORT.
    # 'persist=True' tells the tracker that the current image or frame is the next in a sequence.
    results = model.track(source=video_path, show=True, tracker="bytetrack.yaml", persist=True)

    # Note: The 'results' generator will yield frame-by-frame results.
    # The 'show=True' argument will display the video with tracking annotations.
    # If you want to process frames manually:
    # for r in model.track(source=video_path, stream=True, persist=True):
    #     annotated_frame = r.plot() # r.plot() returns an annotated frame
    #     # Access tracked objects:
    #     if r.boxes.id is not None: # Check if tracking IDs are present
    #         object_ids = r.boxes.id.int().cpu().tolist()
    #         print(f"Tracked object IDs: {object_ids}")
    #
    #     cv2.imshow("YOLOv8 Tracking", annotated_frame)
    #     if cv2.waitKey(1) & 0xFF == ord('q'):
    #         break
    # cv2.destroyAllWindows()
    ```

    _(Ensure you have a video file at `path_to_your_video.mp4` or update the path. You can also use an integer like `0` for your default webcam as the `source`)_.

    When tracking, the output from Ultralytics YOLO includes object IDs along with the bounding boxes and class labels. This ID helps in maintaining the identity of an object across multiple frames [1](https://docs.ultralytics.com/modes/track/), 3. You can use these IDs and bounding box center points to plot the movement trails of objects 3.

### Reference Links

* **Ultralytics YOLO Documentation (Tracking):** [https://docs.ultralytics.com/modes/track/](https://docs.ultralytics.com/modes/track/) [1](https://docs.ultralytics.com/modes/track/)
* **PyImageSearch - Object Tracking with YOLOv8:** [https://pyimagesearch.com/2024/06/17/object-tracking-with-yolov8-and-python/](https://pyimagesearch.com/2024/06/17/object-tracking-with-yolov8-and-python/) [6](https://pyimagesearch.com/2024/06/17/object-tracking-with-yolov8-and-python/)
* **YouTube - Multi-Object Tracking with Ultralytics YOLO:** [https://www.youtube.com/watch?v=vi2K3NmKHfA](https://www.youtube.com/watch?v=vi2K3NmKHfA) 3
* **Encord - YOLO Object Detection Explained:** [https://encord.com/blog/yolo-object-detection-guide/](https://encord.com/blog/yolo-object-detection-guide/) [5](https://encord.com/blog/yolo-object-detection-guide/)
* **Neptune.ai - Object Detection with YOLO:** [https://neptune.ai/blog/object-detection-with-yolo-hands-on-tutorial](https://neptune.ai/blog/object-detection-with-yolo-hands-on-tutorial) [7](https://neptune.ai/blog/object-detection-with-yolo-hands-on-tutorial)
* **GitHub - YOLO Object Detection with OpenCV (YOLOv3 example):** [https://github.com/yash42828/YOLO-object-detection-with-OpenCV](https://github.com/yash42828/YOLO-object-detection-with-OpenCV) [2](https://github.com/yash42828/YOLO-object-detection-with-OpenCV)
* **Core Electronics - YOLO on Raspberry Pi AI Hat:** [https://core-electronics.com.au/guides/yolo-object-detection-on-the-raspberry-pi-ai-hat-writing-custom-python/](https://core-electronics.com.au/guides/yolo-object-detection-on-the-raspberry-pi-ai-hat-writing-custom-python/)&#x20;
