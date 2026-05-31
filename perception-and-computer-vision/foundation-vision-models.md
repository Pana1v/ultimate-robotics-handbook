---
icon: eye
---

# Foundation Vision Models for Robotics

Classical CV (OpenCV, hand-tuned feature detectors, COCO-trained YOLOs) still ships on robots - but if you're building anything new in 2025-2026, your perception stack almost certainly includes a foundation model somewhere. They give you open-vocabulary detection, zero-shot segmentation, dense semantic features, and monocular depth - capabilities that previously required a labeled dataset and a week of training per class.

The catch: these models are big, and robots are not GPUs. Most of the work is figuring out how to run them at robot-relevant rates, or how to distill what they know into something small enough for an Orin.

This page covers the models you'll actually encounter on a robot in 2026, how to deploy them, and the latency you should expect.

### 1. What "foundation model" means here

A foundation vision model is one trained at internet scale (hundreds of millions to billions of images), usually self-supervised or weakly-supervised, that you use either:

* **Zero-shot**: prompt it (text, point, box) and get results without fine-tuning.
* **As a feature extractor**: take its intermediate features and train a small head for your task.
* **As a teacher**: distill it into a smaller, faster student model that runs on-robot.

The shift from task-specific models (a YOLO trained on your boxes) to foundation models (a SAM that segments anything you point at) is the biggest change in robot perception since deep learning replaced SIFT.

### 2. Segment Anything (SAM) and SAM 2

**SAM** (Meta AI, 2023) is a promptable segmentation model. You give it a point, a box, or text (via Grounded-SAM), and it returns a mask. Trained on the SA-1B dataset (1.1 billion masks across 11 million images), it segments objects it has never seen.

* Paper: [arxiv.org/abs/2304.02643](https://arxiv.org/abs/2304.02643)
* Code: [github.com/facebookresearch/segment-anything](https://github.com/facebookresearch/segment-anything)

**SAM 2** (Meta AI, 2024) extends SAM to video with a memory module - you click an object in one frame and it tracks/segments through the rest of the video. This is huge for robots because most robot perception is video, not photos.

* Paper: [arxiv.org/abs/2408.00714](https://arxiv.org/abs/2408.00714)
* Code: [github.com/facebookresearch/sam2](https://github.com/facebookresearch/sam2)

**Where SAM shines on robots:**

* Object isolation for grasping (segment the object, get a clean mask, lift to 3D with depth).
* Bootstrapping training data - segment everything, then label classes by clustering DINOv2 features.
* Interactive teleoperation: operator clicks once, robot tracks and segments through the task.

**Where SAM struggles:**

* Pure SAM has no semantics - it segments "things" but doesn't know what they are. Pair with CLIP/Grounding DINO for that.
* The full ViT-H backbone is slow. Use MobileSAM, FastSAM, or EfficientSAM for on-robot inference.

| Variant       | Backbone      | Params | Source                                                                                              |
| ------------- | ------------- | ------ | --------------------------------------------------------------------------------------------------- |
| SAM ViT-H     | ViT-Huge      | ~636M  | [github.com/facebookresearch/segment-anything](https://github.com/facebookresearch/segment-anything) |
| SAM ViT-B     | ViT-Base      | ~91M   | same                                                                                                |
| MobileSAM     | TinyViT       | ~9.7M  | [github.com/ChaoningZhang/MobileSAM](https://github.com/ChaoningZhang/MobileSAM)                    |
| FastSAM       | YOLOv8-seg    | ~68M   | [github.com/CASIA-IVA-Lab/FastSAM](https://github.com/CASIA-IVA-Lab/FastSAM)                        |
| EfficientSAM  | ViT-Tiny/Small| ~10M/26M| [github.com/yformer/EfficientSAM](https://github.com/yformer/EfficientSAM)                          |
| SAM 2 (Hiera) | Hiera-L/B/S/T | varies | [github.com/facebookresearch/sam2](https://github.com/facebookresearch/sam2)                        |

### 3. Grounding DINO - open-vocabulary detection

**Grounding DINO** (IDEA Research, 2023) takes a text prompt and an image and returns bounding boxes for whatever you described. No training, no fixed class list. "yellow forklift" → boxes around yellow forklifts.

* Paper: [arxiv.org/abs/2303.05499](https://arxiv.org/abs/2303.05499)
* Code: [github.com/IDEA-Research/GroundingDINO](https://github.com/IDEA-Research/GroundingDINO)

Combine it with SAM and you get **Grounded-SAM**: "person wearing a hard hat" → segmentation mask. This is the workhorse for setting up training datasets without manual labeling.

* Grounded-SAM repo: [github.com/IDEA-Research/Grounded-Segment-Anything](https://github.com/IDEA-Research/Grounded-Segment-Anything)

**Grounding DINO 1.5 / 1.6** (2024) improves both speed and accuracy. There's also **YOLO-World** ([arxiv.org/abs/2401.17270](https://arxiv.org/abs/2401.17270)) which is much faster but somewhat less accurate - good when you need real-time open-vocab detection on a robot.

**Practical pattern**: use Grounding DINO offline to auto-label your dataset, then train a small YOLO for on-robot inference. The foundation model is your data engine, not your inference engine.

### 4. CLIP, OpenCLIP, SigLIP - vision-language embeddings

**CLIP** (OpenAI, 2021) learns a joint image-text embedding space by contrastive training on 400M image-text pairs. Result: you can compare an image and a text caption by cosine similarity. No image classifier needed - just compute the embedding of "a photo of a wrench" and compare to your camera frame.

* Paper: [arxiv.org/abs/2103.00020](https://arxiv.org/abs/2103.00020)
* Code: [github.com/openai/CLIP](https://github.com/openai/CLIP)

**OpenCLIP** (LAION) is the open reimplementation, trained on LAION-2B and larger. Often better than original CLIP for downstream tasks.

* Code: [github.com/mlfoundations/open\_clip](https://github.com/mlfoundations/open_clip)

**SigLIP** (Google, 2023) replaces CLIP's softmax contrastive loss with a sigmoid loss - trains better at scale and works well at smaller batch sizes. **SigLIP 2** (2025) is the current go-to.

* SigLIP paper: [arxiv.org/abs/2303.15343](https://arxiv.org/abs/2303.15343)
* SigLIP 2 paper: [arxiv.org/abs/2502.14786](https://arxiv.org/abs/2502.14786)

**On a robot:**

* Open-vocab classification: "is this a forklift, a pallet, or a person?" - embed all three captions, compare to image, pick max.
* Retrieval: given a target description, search the robot's memory of camera frames.
* Reward signal for RL: CLIP similarity between observation and goal description.
* Part of larger VLAs (vision-language-action models) - CLIP/SigLIP is usually the image encoder.

### 5. DINOv2 - self-supervised visual features

**DINOv2** (Meta AI, 2023) is the current best self-supervised visual feature extractor. No text, no labels - just images. The features it produces are dense, semantically meaningful, and transfer well to almost any downstream task (depth, segmentation, classification, correspondence).

* Paper: [arxiv.org/abs/2304.07193](https://arxiv.org/abs/2304.07193)
* Code: [github.com/facebookresearch/dinov2](https://github.com/facebookresearch/dinov2)

**Why robots care:**

* Dense pixel-level features → correspondence across views (no SIFT/SuperPoint needed for many tasks).
* Features cluster by semantic identity even without labels - great for unsupervised object discovery.
* Used as the backbone for Depth Anything, many VLAs, and lots of policy learning work.

**DINOv3** (2025) extends this further with better scaling and longer-range features `[verify]`.

DINOv2 is what you reach for when you want "the best general visual representation, no language needed." If your task is geometric (correspondence, depth, tracking), DINOv2 features are often better than CLIP's because CLIP collapses things into a language-aligned space that loses fine spatial detail.

### 6. Depth Anything v2 - monocular depth

**Depth Anything** (HKU + TikTok, 2024) and **Depth Anything v2** push monocular depth estimation to genuinely useful quality. They train on a mix of labeled and unlabeled images with a DINOv2 backbone and produce surprisingly sharp, consistent relative depth maps from a single RGB image.

* Depth Anything paper: [arxiv.org/abs/2401.10891](https://arxiv.org/abs/2401.10891)
* Depth Anything v2 paper: [arxiv.org/abs/2406.09414](https://arxiv.org/abs/2406.09414)
* Code: [github.com/DepthAnything/Depth-Anything-V2](https://github.com/DepthAnything/Depth-Anything-V2)

**Reality check**: monocular depth from a single image is relative, not metric, out of the box. For most robotics you need metric depth - either fine-tune on a metric dataset, fuse with a sparse stereo/LiDAR signal, or use the metric variant ("Depth Anything V2 Metric"). See [3d-perception.md](3d-perception.md) for how monocular depth slots into 3D perception pipelines.

Other options worth knowing:

* **MiDaS** (Intel ISL) - the predecessor, still common: [github.com/isl-org/MiDaS](https://github.com/isl-org/MiDaS).
* **Marigold** - diffusion-based depth, beautiful results but slow: [arxiv.org/abs/2312.02145](https://arxiv.org/abs/2312.02145).
* **UniDepth** - metric monocular depth without test-time scaling tricks: [arxiv.org/abs/2403.18913](https://arxiv.org/abs/2403.18913).

### 7. Inference cost on Jetson Orin / desktop GPU

This is the actually-important table. Numbers below are rough orders of magnitude - your mileage varies based on input resolution, precision (FP32/FP16/INT8), and TensorRT optimization. Treat them as "what to expect" not "what you will measure."

| Model                  | RTX 4090 (FP16)   | Jetson Orin NX 16GB (FP16) | Jetson Orin Nano 8GB (FP16) | Notes                                                  |
| ---------------------- | ----------------- | -------------------------- | --------------------------- | ------------------------------------------------------ |
| SAM ViT-H              | ~3-6 FPS          | ~0.3-0.8 FPS               | OOM / unusable              | Use MobileSAM/EfficientSAM instead `[verify]`          |
| MobileSAM              | ~30-50 FPS        | ~10-15 FPS                 | ~4-6 FPS                    | Good for on-robot interactive segmentation `[verify]`  |
| FastSAM                | ~25-40 FPS        | ~8-12 FPS                  | ~3-5 FPS                    | YOLO-based, faster than SAM ViT-H `[verify]`           |
| SAM 2 (Hiera-Tiny)     | ~30-45 FPS        | ~6-10 FPS                  | ~2-3 FPS                    | Video tracking, single object `[verify]`               |
| Grounding DINO         | ~5-10 FPS         | ~1-2 FPS                   | OOM-prone                   | Use offline for labeling, not on-robot `[verify]`      |
| YOLO-World v2          | ~60-120 FPS       | ~15-30 FPS                 | ~6-10 FPS                   | Real-time open-vocab detection `[verify]`              |
| CLIP ViT-B/32          | ~500+ FPS         | ~60-100 FPS                | ~25-40 FPS                  | Embedding only, no decoding `[verify]`                 |
| CLIP ViT-L/14          | ~150 FPS          | ~20-30 FPS                 | ~5-10 FPS                   | Bigger backbone `[verify]`                             |
| SigLIP B/16            | ~200+ FPS         | ~30-50 FPS                 | ~10-15 FPS                  | `[verify]`                                             |
| DINOv2 ViT-S/14        | ~200 FPS          | ~25-40 FPS                 | ~10-15 FPS                  | Distilled small variant `[verify]`                     |
| DINOv2 ViT-L/14        | ~50-80 FPS        | ~5-10 FPS                  | ~2-3 FPS                    | `[verify]`                                             |
| Depth Anything v2 Small| ~40-80 FPS        | ~10-15 FPS                 | ~4-6 FPS                    | At 518x518 input `[verify]`                            |
| Depth Anything v2 Large| ~10-20 FPS        | ~2-3 FPS                   | sub-1 FPS                   | `[verify]`                                             |

**Hard-won lessons:**

1. **TensorRT or bust on Jetson.** PyTorch eager mode on Orin is typically 3-10x slower than a TensorRT-optimized engine. Use `torch2trt`, `onnx → trtexec`, or NVIDIA's [Isaac ROS DNN inference](https://github.com/NVIDIA-ISAAC-ROS/isaac_ros_dnn_inference) which wraps this for ROS 2.
2. **FP16 is free accuracy-wise** for almost all of these models. INT8 needs calibration data and sometimes hurts SAM-like models - measure don't assume.
3. **Resolution dominates.** Halving input resolution roughly quadruples throughput. Crop or downsample aggressively before inference.
4. **Batch size 1 is the worst case.** Robots usually need batch 1 (single camera, low latency). The numbers above assume that - desktop GPUs look way better when you batch.

### 8. Distillation strategies for on-robot deployment

You almost never deploy the foundation model directly. The pattern that actually works:

* **Pseudo-labeling**: run the big model offline on your robot's video. Train a small task-specific model (YOLOv8, MobileNetV3 head on DINOv2-distilled features) on those pseudo-labels.
* **Feature distillation**: train a small student CNN to match DINOv2 features on your data. The student is 10-100x faster and gives you most of DINOv2's transfer power.
* **Task heads on frozen backbones**: freeze a small DINOv2-S, add a 3-layer head for your specific task, train the head on a few hundred labeled examples.
* **Compile, quantize, fuse**: TensorRT + FP16 + layer fusion. INT8 after calibration if you can stomach the accuracy loss.

The general rule I follow: **the big model labels the data, the small model runs on the robot.** Even when "the small model" is just a distilled version of the big model, you almost never run the original on production hardware.

### 9. ROS 2 integration patterns

There are three reasonable paths to get a foundation model into a ROS 2 system. Pick based on whether you're on NVIDIA hardware, doing rapid prototyping, or building a production stack.

#### 9.1 Isaac ROS DNN inference (production NVIDIA)

NVIDIA's [Isaac ROS DNN inference](https://github.com/NVIDIA-ISAAC-ROS/isaac_ros_dnn_inference) gives you TensorRT-backed nodes with sensible message types. Wraps the model as a regular ROS 2 component, accepts `sensor_msgs/Image`, publishes detections/masks. Best path on Jetson because it pipes through GXF/NITROS for zero-copy GPU buffers.

There are also Isaac-ROS-specific repos for [foundation pose](https://github.com/NVIDIA-ISAAC-ROS/isaac_ros_foundationpose), [SAM-style segmentation](https://github.com/NVIDIA-ISAAC-ROS/isaac_ros_image_segmentation), and DNN inference templates.

#### 9.2 jetson-inference / jetson-containers (prototyping on Jetson)

dusty-nv's [jetson-inference](https://github.com/dusty-nv/jetson-inference) and [jetson-containers](https://github.com/dusty-nv/jetson-containers) provide pre-built TensorRT-optimized containers for many foundation models. Great for getting something running same-day. Less integrated with ROS 2 but you can wrap them in a thin rclpy node.

#### 9.3 Custom rclpy wrapper (rapid iteration)

For development on a desktop or when you want full control, a minimal pattern:

```python
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import torch
from segment_anything import sam_model_registry, SamPredictor

class SamSegmenterNode(Node):
    def __init__(self):
        super().__init__('sam_segmenter')
        self.declare_parameter('model_type', 'vit_b')
        self.declare_parameter('checkpoint', '/models/sam_vit_b.pth')

        model_type = self.get_parameter('model_type').value
        ckpt = self.get_parameter('checkpoint').value

        sam = sam_model_registry[model_type](checkpoint=ckpt).to('cuda').eval()
        self._predictor = SamPredictor(sam)
        self._bridge = CvBridge()

        self._sub = self.create_subscription(
            Image, '/camera/image_raw',
            self._image_cb, qos_profile_sensor_data)
        self._pub = self.create_publisher(Image, '/sam/mask', 10)

    @torch.inference_mode()
    def _image_cb(self, msg: Image):
        img = self._bridge.imgmsg_to_cv2(msg, desired_encoding='rgb8')
        self._predictor.set_image(img)
        # ... do prompt-based segmentation, publish mask ...

def main():
    rclpy.init()
    node = SamSegmenterNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
```

A few things that bite people:

* **Don't load the model in the constructor on the executor thread** - it blocks discovery. Load lazily on first callback or in a separate setup thread.
* **Use `qos_profile_sensor_data` for the image subscription** - best-effort, depth 5, matches camera publishers.
* **`@torch.inference_mode()`** on the callback is non-negotiable. Saves memory and ~5-15% latency vs `torch.no_grad()`.
* **Pin the GPU buffer** - copying CPU↔GPU per frame at 30 Hz will dominate latency. Use CUDA-aware cv\_bridge or NITROS on Jetson.
* **Throttle the publisher**. The model is your bottleneck; the subscriber will queue images. Drop frames intentionally with a deadline or use a `last_message` pattern.

#### 9.4 Hugging Face Transformers in rclpy

For CLIP/SigLIP/Grounding DINO, the easiest path is `transformers`:

```python
from transformers import AutoProcessor, AutoModel
import torch

processor = AutoProcessor.from_pretrained('google/siglip-base-patch16-224')
model = AutoModel.from_pretrained('google/siglip-base-patch16-224').to('cuda').eval()

texts = ['a photo of a forklift', 'a photo of a pallet', 'a photo of a person']
text_inputs = processor(text=texts, return_tensors='pt', padding='max_length').to('cuda')

with torch.inference_mode():
    text_embeds = model.get_text_features(**text_inputs)
    text_embeds = text_embeds / text_embeds.norm(dim=-1, keepdim=True)
    # cache text_embeds - they don't change per frame

# per camera frame:
image_inputs = processor(images=frame, return_tensors='pt').to('cuda')
with torch.inference_mode():
    image_embeds = model.get_image_features(**image_inputs)
    image_embeds = image_embeds / image_embeds.norm(dim=-1, keepdim=True)
    scores = (image_embeds @ text_embeds.T).softmax(dim=-1)
```

**Cache text embeddings.** The text side of CLIP/SigLIP is fixed per prompt set - encoding it on every frame is the rookie mistake. Encode once at startup, store the tensor, multiply on every frame.

### 10. When to reach for which model

Use this as a decision table when designing perception:

| Task                                           | Reach for                            |
| ---------------------------------------------- | ------------------------------------ |
| "I need bounding boxes for novel objects"      | Grounding DINO (offline) → YOLO-World (online) |
| "I need a mask for the object I'm grasping"    | SAM 2 (interactive) or MobileSAM     |
| "What is this object?" with a fixed vocabulary | SigLIP / OpenCLIP zero-shot          |
| "I want robust visual features for downstream" | DINOv2 (frozen backbone + small head) |
| "I need depth from a single RGB image"         | Depth Anything v2                    |
| "I need to track an object through video"      | SAM 2                                |
| "I need to label 10k images fast"              | Grounded-SAM (Grounding DINO + SAM)  |
| "I need this on a robot at 30 FPS"             | None of the above directly - distill |

### 11. Further reading

* Awesome SAM list: [github.com/Hedlen/awesome-segment-anything](https://github.com/Hedlen/awesome-segment-anything)
* Awesome foundation models for robotics: [github.com/JeffreyYH/Awesome-Generalist-Robots-via-Foundation-Models](https://github.com/JeffreyYH/Awesome-Generalist-Robots-via-Foundation-Models)
* Isaac ROS overview: [nvidia-isaac-ros.github.io](https://nvidia-isaac-ros.github.io/)
* Foundation models for robotics survey (Firoozi et al.): [arxiv.org/abs/2312.07843](https://arxiv.org/abs/2312.07843)
* For 3D foundation models (point clouds, NeRF, Gaussian Splatting), see [3d-perception.md](3d-perception.md).
