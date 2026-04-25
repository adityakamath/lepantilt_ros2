# Pan Tilt 100 ROS 2 Driver

![Project Status](https://img.shields.io/badge/Status-Active-green)
![ROS 2](https://img.shields.io/badge/ROS%202-Kilted%20(Ubuntu%2024.04)-blue?style=flat&logo=ros&logoSize=auto)
[![Ask DeepWiki (Experimental)](https://deepwiki.com/badge.svg)](https://deepwiki.com/adityakamath/pt100_ros2)
[![Blog](https://img.shields.io/badge/Blog-kamathrobotics.com-darkorange?style=flat&logo=hashnode&logoSize=auto)](https://kamathrobotics.com)
![License](https://img.shields.io/github/license/adityakamath/pt100_ros2?label=License)

ROS 2 software stack for a 2-DOF pan-tilt camera mount using [SO-ARM100](https://github.com/TheRobotStudio/SO-ARM100) parts, [Feetech STS3215](https://www.feetechrc.com/STS3215.html) servo motors and an [OAK-D S2](https://docs.luxonis.com/hardware/products/OAK-D-S2) camera. Provides position control with joystick teleop, visual-inertial odometry (VIO) bringup, and an embeddable xacro module for integration into other robots.

**⚠️ Status:** Tested and validated using reference hardware with ROS 2 Kilted on Ubuntu 24.04 running on a Raspberry Pi 5. Needs motor calibration and serial port configuration before use.

## Hardware Requirements

| Component      | Details                                                                                   |
|----------------|-------------------------------------------------------------------------------------------|
| Pan motor      | [Feetech STS3215](https://www.feetechrc.com/STS3215.html), Motor ID `1`                  |
| Tilt motor     | Feetech STS3215, Motor ID `2`                                                             |
| Servo driver   | [Waveshare Bus Servo Adapter A](https://www.waveshare.com/bus-servo-adapter-a.htm)  |
| Camera         | [OAK-D S2](https://docs.luxonis.com/hardware/products/OAK-D-S2)                   |
| Structural     | 3D printed Base and shoulder parts from [SO-ARM100](https://github.com/TheRobotStudio/SO-ARM100)     |
| Camera mount   | 3D printed OAK-D S2 bracket (STL in [`pt100_description/meshes/`](pt100_description/meshes/)) |

Both motors are chained together on a single serial bus at 1 Mbaud, connected to the host via the Waveshare servo driver. The URDF is dimensioned from SO100 parts; parts from either SO100 or SO101 are compatible.

| Parameter   | Launch argument | Argument value  | URDF default   |
|-------------|-----------------|-----------------|----------------|
| Serial port | `serial_port`   | `/dev/ttySERVO` | `/dev/ttyACM0` |

`/dev/ttySERVO` is a user-created udev symlink set as the default in [`pt100_control/launch/pantilt.launch.py`](pt100_control/launch/pantilt.launch.py). Identify your actual device (commonly `/dev/ttyACM0` or `/dev/ttyUSB0`) and pass it with the `serial_port` argument, or update the default in the launch file.

### Motor Calibration

Each motor has a **center position** (in raw steps, 0–4095) that maps to 0 rad in the URDF. The defaults below are the launch argument values and match the reference hardware build; must be recalibrated since other physical assemblies will differ.

| Joint      | Launch argument      | Argument value | URDF default |
|------------|----------------------|----------------|--------------|
| Pan        | `pan_center_steps`   | `2048`         | `2048`       |
| Tilt       | `tilt_center_steps`  | `2646`         | `2048`       |

Pass updated values at launch:

```bash
ros2 launch pt100_control pantilt.launch.py pan_center_steps:=2100 tilt_center_steps:=2700
```

Or make the change permanent by editing the defaults in [`pt100_control/launch/pantilt.launch.py`](pt100_control/launch/pantilt.launch.py).

## Dependencies

- **[ROS 2 Kilted](https://docs.ros.org/en/kilted/)** — other distributions untested
- **[ros2_control](https://control.ros.org/)** — controller manager, joint state broadcaster, forward command controller
- **[sts_hardware_interface](https://github.com/adityakamath/sts_hardware_interface)** — hardware interface for Feetech STS servo motors
- **[depthai-ros](https://github.com/luxonis/depthai-ros)** — DepthAI ROS 2 driver for the OAK-D S2 Camera
- **[joy_teleop](https://index.ros.org/p/joy_teleop/)** — joystick-to-topic bridge (included in this package's launch)

> **Joystick:** `joy_teleop` is included but the [`joy`](https://github.com/ros-drivers/joystick_drivers) node is **not** — it must be started separately (on the same or a networked device) before the system will respond to controller input:
> ```bash
> ros2 run joy joy_node
> ```

## Installation

```bash
cd <your workspace>/src
git clone https://github.com/adityakamath/pantilt100_ros2.git
git clone https://github.com/adityakamath/sts_hardware_interface.git

cd ..
colcon build --packages-select pt100_description pt100_control pt100_bringup sts_hardware_interface

source install/setup.bash
```

## Usage

### Control stack only (no camera)

```bash
ros2 launch pt100_control pantilt.launch.py
```

### Camera driver only (no control stack)

```bash
ros2 launch pt100_bringup oakd.launch.py
```

### Full PR100 bringup (control + OAK-D S2 camera)

```bash
ros2 launch pt100_bringup pt100.launch.py
```

### Mock mode (no hardware required)

```bash
ros2 launch pt100_control pantilt.launch.py use_mock:=true
```

### Launch arguments

| Argument            | Package             | Default          | Description                                        |
|---------------------|---------------------|------------------|----------------------------------------------------|
| `serial_port`       | `pt100_control` | `/dev/ttySERVO`  | Serial port for STS motor communication            |
| `use_mock`          | both                | `false`          | Run without hardware (simulated motor responses)   |
| `use_sync_write`    | `pt100_control` | `true`           | Coordinated SyncWrite for simultaneous motor moves |
| `pan_center_steps`  | `pt100_control` | `2048`           | Raw step value that maps to 0 rad on pan axis      |
| `tilt_center_steps` | `pt100_control` | `2646`           | Raw step value that maps to 0 rad on tilt axis     |
| `diagnostics`       | both                | `true`           | Launch motor diagnostics node                      |
| `pointcloud`        | `pt100_bringup` | `false`          | Enable RGBD point cloud pipeline on OAK-D S2       |

> **Note:** `pt100_bringup` only forwards `use_mock` and `diagnostics` to the control stack — `serial_port`, `use_sync_write`, `pan_center_steps`, and `tilt_center_steps` use their `pt100_control` launch defaults when launched via bringup.
>
> `serial_port` has two layers of defaults: the launch file default is `/dev/ttySERVO` (udev symlink used with the reference hardware); the xacro default (used when invoking xacro directly, without the launch file) is `/dev/ttyACM0`. 
>
> Similarly, `pan_center_steps` and `tilt_center_steps` default to `2048` in the xacro, with the calibrated tilt value (`2646`) set in the launch file for the reference hardware.
>
> Motor IDs (`pan_motor_id`, `tilt_motor_id`) and baud rate are **xacro-only parameters** — the launch files do not forward them. Change them permanently in [`pantilt.control.xacro`](pt100_description/urdf/pantilt.control.xacro).

## Package Structure

```text
pt100_ros2/
├── pt100_description/       # URDF model and meshes
│   ├── urdf/
│   │   ├── pantilt.common.xacro     # Geometry constants and visual offsets
│   │   ├── pantilt.control.xacro    # ros2_control block, motor parameters, joint limits
│   │   ├── pantilt.module.xacro     # Links and joints as an embeddable xacro macro
│   │   ├── pantilt.urdf.xacro       # Standalone entry point (includes all three above)
│   │   ├── oakd_s2.urdf.xacro       # OAK-D S2 camera and IMU macro
│   │   └── pantilt.urdf             # Pre-generated URDF for external tools (not used at runtime)
│   └── meshes/                      # STL files for pan-tilt body and OAK-D S2
│
├── pt100_control/           # Controllers, config, and launch files
│   ├── config/
│   │   ├── pantilt_control_config.yaml  # Controller manager, spawner types, joint limits
│   │   └── teleop_config.yaml           # joy_teleop axis/button mapping
│   └── launch/
│       ├── pantilt.launch.py    # Control stack (RSP, controller_manager, spawners, teleop)
│       └── teleop.launch.py     # joy_teleop node in isolation
│
└── pt100_bringup/           # System-level launch files and camera config
    ├── config/
    │   ├── vio.yaml             # OAK-D S2: RGBD pipeline + VIO at 60 Hz, no point cloud
    │   └── vio_pcl.yaml         # OAK-D S2: same as above with RGBD point cloud enabled
    └── launch/
        ├── pt100.launch.py    # Full PT100 system: includes pt100_control + oakd
        └── oakd.launch.py    # OAK-D S2 camera driver only
```

## Package Details

### pt100_description

The URDF is split across four xacro files with distinct responsibilities:

| File                      | Purpose                                                                 |
|---------------------------|-------------------------------------------------------------------------|
| `pantilt.common.xacro`    | Visual offsets, mesh colours, joint origins, camera mount position      |
| `pantilt.control.xacro`   | Launch args, motor velocity/torque limits, joint limits, `ros2_control` block |
| `pantilt.module.xacro`    | All links and joints wrapped in a `pt100_module` xacro macro        |
| `pantilt.urdf.xacro`      | Standalone robot: creates `base_footprint`, instantiates the macro      |

Both pan and tilt joints use `velocity="1e6"` in their URDF `<limit>` elements. See [Design](#architecture) for the reason.

### pt100_control

The `pantilt_controller` uses a [`ForwardCommandController`](https://control.ros.org/master/doc/ros2_controllers/forward_command_controller/doc/userdoc.html) on the `position` interface. Each cycle it forwards the commanded position directly to the hardware interface, which translates it to motor steps. Velocity profiling is handled by the STS3215 motor firmware, not in software.

The [`JointStateBroadcaster`](https://control.ros.org/master/doc/ros2_controllers/joint_state_broadcaster/doc/userdoc.html) publishes standard joint states plus extended per-joint diagnostics (voltage, temperature, current, moving flag) to `/dynamic_joint_states`.

**Teleop mapping** (`teleop_config.yaml`):

| Input            | Button / Axis | Action                                 |
|------------------|---------------|----------------------------------------|
| Deadman          | L1 (button 9) | Enable motion — hold to send commands  |
| Left stick X     | Axis 0        | Pan position (±π/2 rad at full deflection) |
| Left stick Y     | Axis 1        | Tilt position (±π/2 rad at full deflection) |
| A (button 0)     | —             | Call `/emergency_stop` → enable        |
| B (button 1)     | —             | Call `/emergency_stop` → disable       |

Joystick axes map directly to **absolute** joint positions, not velocities. The full axis range ±1 maps to ±π/2 rad.

### pt100_bringup

`pt100.launch.py` composes `pt100_control/pantilt.launch.py` and `oakd.launch.py` and forwards the relevant arguments to each.

`oakd.launch.py` launches the OAK-D S2 as a composable node. Two pipeline configurations are available:

| Config file   | Pipeline                          | Use case                        |
|---------------|-----------------------------------|---------------------------------|
| `vio.yaml`    | RGBD + VIO at 60 Hz               | Default — odometry and tracking |
| `vio_pcl.yaml`| RGBD + VIO + point cloud          | 3D mapping (higher CPU load)    |

Set `DEPTHAI_DEBUG=1` in the environment before launching to enable debug-level logging from the camera driver.

## ROS Interfaces

### Topics

| Topic                            | Type                                    | Direction  | Description                                    |
|----------------------------------|-----------------------------------------|------------|------------------------------------------------|
| `/joint_states`                  | `sensor_msgs/JointState`                | Published  | Pan and tilt position, velocity, effort        |
| `/dynamic_joint_states`          | `control_msgs/DynamicJointState`        | Published  | Extended states: voltage, temperature, current, is_moving |
| `/pantilt_controller/commands`   | `std_msgs/Float64MultiArray`            | Subscribed | Position commands `[pan_rad, tilt_rad]`        |
| `/joy`                           | `sensor_msgs/Joy`                       | Subscribed | Joystick input (published by external `joy` node) |
| `/oak/rgb/image_raw`             | `sensor_msgs/Image`                     | Published  | OAK-D S2 RGB stream                            |
| `/oak/stereo/image_raw`          | `sensor_msgs/Image`                     | Published  | OAK-D S2 depth stream                          |
| `/oak/imu/data`                  | `sensor_msgs/Imu`                       | Published  | OAK-D S2 IMU data                              |
| `/oak/vio/transform`             | `geometry_msgs/TransformStamped`        | Published  | Visual-inertial odometry output                |

### TF Frames

```text
base_footprint                  ← standalone root (pantilt.urdf.xacro only)
└── pantilt_base_link           ← physical mount base (pantilt_mount_joint when embedded)
    └── pan_link                ← rotates about Z (pan_joint, ±90°)
        └── tilt_link           ← rotates about Z in reoriented frame (tilt_joint, ±90°)
            └── oak_link        ← OAK-D S2 optical centre
                ├── oak_link_model_origin   ← mesh visual origin
                └── oak_imu_frame           ← OAK-D S2 IMU frame
```

## Embedding as a Module

The pan-tilt is designed to be mounted on another robot. Include `pantilt.control.xacro` and `pantilt.module.xacro` in the host robot's URDF, then instantiate the macro with the desired parent link and mount origin:

```xml
<!-- In the host robot's URDF xacro -->
<xacro:include filename="$(find pt100_description)/urdf/pantilt.control.xacro"/>
<xacro:include filename="$(find pt100_description)/urdf/pantilt.module.xacro"/>

<xacro:pt100_module parent="base_link">
  <origin xyz="0.0 0.0 0.15" rpy="0 0 0"/>
</xacro:pt100_module>
```

In the host robot's controller config, add `has_velocity_limits: false` for the pan and tilt joints under `controller_manager.ros__parameters.joint_limits` to prevent spurious rate-limiting errors (see [Design](#architecture)):

```yaml
controller_manager:
  ros__parameters:
    joint_limits:
      pan_joint:
        has_velocity_limits: false
      tilt_joint:
        has_velocity_limits: false
```

The `ros2_control` hardware block is defined in `pantilt.control.xacro` (not inside the macro itself), so no additional hardware interface configuration is needed beyond the above.

## Design

### Xacro module design

The robot model is split into `common` (geometry), `control` (ros2_control + motor parameters), and `module` (links and joints) rather than one flat URDF. This allows the pan-tilt to be embedded into any host robot by including only `control` and `module` — the standalone `pantilt.urdf.xacro` is just a thin wrapper that creates a `base_footprint` root and instantiates the macro.

The `pt100_module` macro takes a `parent` link and an `origin` block. The `pantilt_mount_joint` inside the macro connects `parent` → `pantilt_base_link`, so placement is fully controlled by the caller.

### Position control and velocity limits

`ForwardCommandController` sends raw position targets directly to the hardware. The STS3215 motor firmware manages the velocity profile internally — the motor moves to the target at a configured speed without any software trajectory generation.

`joy_teleop` maps joystick axes to **absolute** position targets (axis position × π/2 rad). When the deadman button is first pressed or the joystick is moved quickly, the commanded target can jump by up to π rad in a single control cycle. ros2_control's `JointSaturationLimiter`, when `enforce_command_limits: true`, would normally clip such jumps using the URDF velocity limit — logging a `Command of at least one joint is out of limits` error on every affected cycle.

To suppress these spurious errors without disabling limit enforcement entirely, both joints use `velocity="1e6"` in their URDF `<limit>` elements (the URDF spec requires a value; `1e6` rad/s is physically unreachable) and `has_velocity_limits: false` in `pantilt_control_config.yaml`. Position limits (±π/2) remain enforced. The motor's own velocity cap (`max_velocity_steps`, defaulting to 50 % of the STS3215 hardware maximum) is the real upper bound on speed.

## Notes and Troubleshooting

**Joystick not working** — The `joy` node is not launched by this package. Start it separately before launching the control stack, or in a second terminal alongside it:

```bash
ros2 run joy joy_node
```

Hold **L1** to enable motion. Without the deadman button held, `joy_teleop` does not publish commands.

**No hardware available** — Use `use_mock:=true` to run the full control stack with simulated motor responses. All topics, TF frames, and controllers behave identically; motor feedback values are synthesised.

**Camera driver debug logging** — Set `DEPTHAI_DEBUG=1` before launching to enable verbose output from `depthai_ros_driver`:

```bash
DEPTHAI_DEBUG=1 ros2 launch pt100_bringup pt100.launch.py
```

**Motor not reaching commanded position** — If a motor is mechanically obstructed or the center step calibration is wrong, the reported position will diverge from the command. Check `/dynamic_joint_states` for elevated `effort` or `current` values, which indicate the motor is stalled.

## License

Apache License 2.0 — see [LICENSE](LICENSE).
