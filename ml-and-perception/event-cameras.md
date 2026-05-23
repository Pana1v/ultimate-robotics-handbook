---
icon: eye
---

# Event Cameras

Conventional cameras sample the entire image plane at a fixed frame rate. Event cameras don't. Each pixel independently and asynchronously reports a "+1" or "-1" event whenever its log-intensity changes by a threshold. The output isn't frames - it's a stream of microsecond-timestamped events.

This sounds like a niche academic toy until you put one on a drone trying to dodge obstacles at 50 m/s, or on a robot in a welding bay, or in a tunnel where headlights occasionally blind a CMOS sensor. Then the latency, dynamic range, and power numbers start to matter a lot.

This page is a working roboticist's introduction to event cameras: where they win, where they lose, and what the software actually looks like.

### 1. What an event camera reports

For each pixel `(x, y)` independently, when log-intensity crosses a threshold, the pixel emits an event `(x, y, t, p)` where `p ∈ {+1, -1}` is polarity (brightening or darkening) and `t` is a microsecond timestamp.

| Property              | Conventional CMOS               | Event camera                      |
| --------------------- | ------------------------------- | --------------------------------- |
| Output                | Frames at fixed rate            | Asynchronous events               |
| Effective rate        | 30-1000 Hz                      | Equivalent to ~10 kHz+            |
| Latency               | Frame period + readout (~ms)    | Microseconds                      |
| Dynamic range         | ~60-80 dB                       | >120 dB                           |
| Bandwidth (static)    | Constant                        | Near zero (no change → no events) |
| Bandwidth (high motion) | Constant                       | Can spike very high               |
| Power                 | ~hundreds of mW                 | Tens of mW typical                |
| Spatial resolution    | High (millions of pixels easy)  | Lower (current high-end ~1MP)     |
| Color                 | Standard                        | Mostly monochrome; color variants exist |

The defining trade is that event cameras are **temporally rich but spatially sparse**, while CMOS cameras are the opposite.

### 2. Hardware

Two main vendors matter in 2026:

#### 2.1 Prophesee (Metavision)

Founded out of Pierre Fabre's CNRS / Vision Institute work. They now ship sensors integrated into Sony silicon (IMX636 and successors). High resolution, robust SDK, used in many industrial applications.

* Site: [www.prophesee.ai](https://www.prophesee.ai/)
* SDK (Metavision): [docs.prophesee.ai](https://docs.prophesee.ai/) `[verify]`
* OpenEB (open-source subset of the SDK): [github.com/prophesee-ai/openeb](https://github.com/prophesee-ai/openeb)

Common sensors:

* **EVK4 (HD)** - 1280×720, IMX636 sensor. The current workhorse for research and high-end industrial.
* **GenX320** - 320×320, very low power. For battery-constrained / IoT use.

#### 2.2 iniVation (DAVIS, DVS)

Spun out of ETH Zürich / Tobi Delbrück's lab. The originators of the DAVIS (Dynamic and Active-pixel Vision Sensor), which combines event output with a co-located low-rate APS (conventional) frame.

* Site: [inivation.com](https://inivation.com/)
* SDK: dv-processing - [gitlab.com/inivation/dv/dv-processing](https://gitlab.com/inivation/dv/dv-processing) `[verify]`

Common sensors:

* **DAVIS 346** - 346×260, events + 346×260 APS frames. The de facto research sensor for years.
* **DVXplorer** - pure event sensor, higher resolution (640×480).

The APS-plus-events feature of the DAVIS line is genuinely useful: you get a low-rate conventional frame for context (running a CNN, doing classical SLAM) plus the high-rate event stream for fast tracking.

### 3. Why event cameras win

The arguments for choosing an event camera, in priority order:

1. **High dynamic range.** >120 dB. Welding sparks, tunnel exits, scrolling through direct sunlight - situations that destroy a CMOS sensor are routine for an event camera.
2. **Microsecond-latency motion sensing.** A frame-based system has at least one frame period of delay before it sees a change. An event camera reports the change as it happens. For high-speed control loops this is decisive.
3. **No motion blur.** Each event is essentially instantaneous. Fast rotors, propellers, or projectiles that turn into smears on a CMOS sensor are crisp on an event sensor.
4. **Low power and low bandwidth in static scenes.** A stationary camera in a quiet room emits almost nothing. Useful for always-on / battery applications.
5. **Sub-frame temporal resolution for vibration sensing, lip reading, ballistic tracking, etc.** Things you literally can't do at 30 Hz.

The places these have shown up in real robotics:

* **High-speed drone obstacle avoidance** (Davide Scaramuzza's group at UZH; see [arxiv.org/abs/2002.05847](https://arxiv.org/abs/2002.05847) for the original "Event-based vision for drones" line of work `[verify]`).
* **Visual-inertial odometry for agile flight.**
* **Industrial inspection** where lighting is bad or the part is moving fast.
* **Particle / spark detection** in monitoring.
* **Eye tracking and gesture sensing** in AR/VR.

### 4. Why event cameras lose

Be honest about where they don't help:

1. **Slow / static scenes.** No motion = no events = no signal. A robot sitting still sees nothing.
2. **Dense reconstruction.** Event cameras are great at edges and motion, terrible at filling in textureless surfaces. You won't build a dense map from events alone.
3. **Anything depending on absolute brightness or color.** Events are differential. They tell you "this pixel got brighter" not "this pixel is RGB(127, 200, 50)."
4. **Off-the-shelf deep learning.** You can't just shove events into a YOLO. Most pretrained models are useless. The ecosystem is maturing, but it's nowhere near as rich as the RGB ecosystem.
5. **Spatial resolution.** Even the current "HD" 1280×720 sensors lag behind the multi-megapixel CMOS norm. You'll lose fine detail.
6. **Cost.** Sensors are several thousand USD. Cameras with comparable spatial resolution in a CMOS form are 10-100x cheaper.

The honest summary: event cameras are a **complement** to conventional vision, not a replacement. The most successful systems use both.

### 5. Working with event data

Event data isn't a frame, so you can't just call OpenCV on it. The standard preprocessing patterns:

* **Time-windowed event frames.** Bin events over a fixed time interval (e.g., 10 ms) and accumulate into a 2-channel (positive / negative) image. Lets you reuse CNNs.
* **Event-count histograms.** Sum events per pixel within a window. Loses temporal ordering but is simple.
* **Time surface.** For each pixel, store the timestamp of the most recent event. Encodes recency.
* **Voxel grids.** Stack short-time event frames into a 3D (x, y, t) tensor.

For deep learning specifically:

* **Spiking Neural Networks (SNNs)** - natural fit for event data, but the deployment story is thin in 2026 except on neuromorphic hardware (Intel Loihi, BrainChip Akida) `[verify]`.
* **Graph Neural Networks** - treat events as a point cloud in (x, y, t) and run a GNN. Used by some research groups, not yet mainstream.
* **Vanilla CNNs on event frames** - most common approach, works fine for many tasks.

### 6. Algorithms and the state of the art

#### 6.1 Feature tracking

Tracking sparse features from event streams. Used as a front-end for VO/VIO/SLAM.

* **eklt** (UZH, 2018) - combined event + frame feature tracking. Code: [github.com/uzh-rpg/rpg\_eklt](https://github.com/uzh-rpg/rpg_eklt) `[verify]`
* **Event-based feature trackers** from the UZH RPG group.

#### 6.2 Optical flow

Estimating per-pixel motion from events.

* **EV-FlowNet** (Zhu et al., RSS 2018) - learning event-based optical flow. [arxiv.org/abs/1802.06898](https://arxiv.org/abs/1802.06898)
* **E-RAFT** (Gehrig et al., 3DV 2021) - adapts RAFT to events, current strong baseline. [arxiv.org/abs/2108.10552](https://arxiv.org/abs/2108.10552) `[verify]`

#### 6.3 Event-based SLAM and VIO

Where event cameras get put to actual work on robots.

* **EVO** (Rebecq et al., 2016) - event-based VO (monocular, no IMU). [arxiv.org/abs/1607.03468](https://arxiv.org/abs/1607.03468) `[verify]`
* **ESVO** (Zhou et al., TRO 2021) - event-based stereo VO. Code: [github.com/HKUST-Aerial-Robotics/ESVO](https://github.com/HKUST-Aerial-Robotics/ESVO) `[verify]`
* **Ultimate SLAM** (Vidal et al., 2018) - events + frames + IMU fused. [arxiv.org/abs/1810.05803](https://arxiv.org/abs/1810.05803) `[verify]`
* **EDS** - event-aided direct sparse odometry. `[verify]`

The best-performing systems pair events with conventional frames and an IMU, because each modality covers the others' failures: events handle fast motion and HDR, frames handle static scenes and texture, IMU handles short-term motion estimation.

#### 6.4 Reconstruction and depth

Mostly research-stage but worth knowing:

* **E2VID** (Rebecq et al., 2019) - reconstruct video from events. [arxiv.org/abs/1906.07165](https://arxiv.org/abs/1906.07165) `[verify]`
* **DSEC dataset** - event + frame + LiDAR driving dataset for benchmarking. [dsec.ifi.uzh.ch](https://dsec.ifi.uzh.ch/) `[verify]`

### 7. Software stacks

#### 7.1 Prophesee Metavision SDK / OpenEB

The Prophesee stack. C++ and Python APIs. Hardware connection, recording, the standard preprocessing operations (frame generation, time surfaces), and a set of demo algorithms.

* OpenEB (the open-source pieces): [github.com/prophesee-ai/openeb](https://github.com/prophesee-ai/openeb)
* Full Metavision SDK is licensed; OpenEB covers most of what you need for research and prototyping.
* ROS 2 driver: [github.com/ros-event-camera/metavision\_driver](https://github.com/ros-event-camera/metavision_driver) `[verify]`

#### 7.2 dv-processing (iniVation)

iniVation's stack for DAVIS / DVXplorer sensors. C++ core, Python bindings, modules for filtering, frame generation, feature detection.

* Repo: [gitlab.com/inivation/dv/dv-processing](https://gitlab.com/inivation/dv/dv-processing) `[verify]`
* ROS 2 driver (dv-ros): [gitlab.com/inivation/dv/dv-ros](https://gitlab.com/inivation/dv/dv-ros) `[verify]`

#### 7.3 ROS 2 integration

There's a community `event_camera_msgs` package for ROS 2 that defines a standard message type for events.

* `event_camera_msgs`: [github.com/ros-event-camera/event\_camera\_msgs](https://github.com/ros-event-camera/event_camera_msgs) `[verify]`
* `event_camera_codecs`: [github.com/ros-event-camera/event\_camera\_codecs](https://github.com/ros-event-camera/event_camera_codecs) `[verify]`

The message type packs events into a compressed format because publishing individual `(x, y, t, p)` events as one ROS 2 message each would obliterate the middleware. Always batch.

#### 7.4 Sample minimal rclpy node

```python
import rclpy
from rclpy.node import Node
from event_camera_msgs.msg import EventPacket  # exact type per chosen msg pkg
import event_camera_codecs as codec  # pseudo-import

class EventPreprocNode(Node):
    def __init__(self):
        super().__init__('event_preproc')
        self._decoder = codec.Decoder()
        self._sub = self.create_subscription(
            EventPacket, '/event_camera/events',
            self._on_packet, 10)
        # accumulate events over a window and emit a frame
        self._window_us = 10_000  # 10 ms
        self._buffer = []
        self._last_emit_us = None

    def _on_packet(self, msg: EventPacket):
        events = self._decoder.decode(msg)   # array of (x, y, t_us, polarity)
        self._buffer.extend(events)
        if self._last_emit_us is None:
            self._last_emit_us = events[0].t
        if events[-1].t - self._last_emit_us >= self._window_us:
            frame = self._accumulate_to_frame(self._buffer)
            self._publish_frame(frame)
            self._buffer.clear()
            self._last_emit_us = events[-1].t
```

The pattern is always: subscribe to event packets, decode, accumulate into a frame-like representation over a time window, then hand off to standard CV.

### 8. When to put an event camera on your robot

A checklist I use:

* The robot needs **microsecond-latency** reaction to visual change. (Drones, fast manipulators, projectile interception.)
* The lighting is **extreme or unpredictable**. (Welding, tunnels, mixed indoor-outdoor, glare.)
* Motion blur from CMOS sensors is **breaking your perception**.
* You need **always-on** vision on a strict power budget.

If none of these apply, an RGB or RGB-D camera is almost certainly the right choice - cheaper, higher-resolution, with a vastly richer software ecosystem.

If at least one applies, an event camera is at least worth a prototype. The pattern I've seen work in practice: **event camera + conventional RGB camera fused**, not event camera alone. The event sensor handles the dynamic-range / motion edge cases; the RGB sensor handles everything else and feeds the foundation-model perception stack.

### 9. Further reading

* Scaramuzza group event vision survey (Gallego et al., TPAMI 2022): [arxiv.org/abs/1904.08405](https://arxiv.org/abs/1904.08405)
* UZH RPG event-camera datasets: [rpg.ifi.uzh.ch/davis\_data.html](https://rpg.ifi.uzh.ch/davis_data.html) `[verify]`
* Awesome event vision: [github.com/uzh-rpg/event-based\_vision\_resources](https://github.com/uzh-rpg/event-based_vision_resources)
* DSEC driving dataset: [dsec.ifi.uzh.ch](https://dsec.ifi.uzh.ch/) `[verify]`
* For conventional CMOS perception, see [cameras-depth-sensors-and-lidar.md](cameras-depth-sensors-and-lidar.md).
* For foundation models that don't yet really exist for event data, see [foundation-vision-models.md](foundation-vision-models.md) - this is a gap, not a finished story.
