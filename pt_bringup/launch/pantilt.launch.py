#!/usr/bin/env python3
"""
Main bringup launch file for the complete Pan Tilt 100 system: mechanism + camera.

This launch file includes:
    - pt_control's pantilt.launch.py (robot control stack)
    - pt_bringup's oakd.launch.py (OAK-D camera)
It forwards relevant launch arguments to each included launch file.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def launch_setup(context):
    """Include pt_control's control stack, plus either oakd (real) or Gazebo (sim)."""
    use_mock     = LaunchConfiguration("use_mock").perform(context)
    sim          = LaunchConfiguration("sim").perform(context).strip().lower() in ("true", "1")
    gui          = LaunchConfiguration("gui").perform(context)
    use_sim_time = LaunchConfiguration("use_sim_time").perform(context)

    if sim:
        # Running in Gazebo implies sim time; keep any explicit use_mock override,
        # otherwise force it so the STS plugin (unused in gazebo mode, but still
        # resolved by xacro defaults) never assumes a real serial port is present.
        use_sim_time = "true"
        use_mock = use_mock or "true"

    pkg_bringup = FindPackageShare("pt_bringup").perform(context)

    pantilt_control_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare("pt_control"),
                "launch",
                "pantilt.launch.py"
            ])
        ),
        launch_arguments={
            "sts_serial_port": LaunchConfiguration("sts_serial_port"),
            "use_mock": use_mock,
            "diagnostics": LaunchConfiguration("diagnostics"),
            "pantilt_config": LaunchConfiguration("pantilt_config"),
            "use_sim_time": use_sim_time,
            "ros2_control_hardware_type": "gazebo" if sim else "real",
        }.items()
    )

    actions = [pantilt_control_launch]

    if sim:
        # Gazebo itself, plus the bridge/spawn plumbing - same pattern as
        # lekiwi_bringup/launch/lekiwi.launch.py. oakd is a real-camera driver with no
        # simulated equivalent yet, so it's skipped here.
        gz_launch_description = IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                [FindPackageShare("ros_gz_sim"), "/launch/gz_sim.launch.py"]
            ),
            launch_arguments={
                "gz_args": " -r -v 4 empty.sdf" if gui.lower() in ("true", "1") else " -s -r -v 4 empty.sdf",
            }.items(),
        )
        gz_sim_bridge = Node(
            package="ros_gz_bridge",
            executable="parameter_bridge",
            arguments=["/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock"],
            output="screen",
        )
        # -topic robot_description subscribes and waits for pt_control's
        # robot_state_publisher to publish it - no ordering dependency needed here.
        gz_spawn_entity = Node(
            package="ros_gz_sim",
            executable="create",
            output="screen",
            arguments=["-topic", "robot_description", "-name", "pantilt", "-allow_renaming", "true"],
        )
        actions += [gz_launch_description, gz_sim_bridge, gz_spawn_entity]
    else:
        oakd_launch = IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([
                    FindPackageShare("pt_bringup"),
                    "launch",
                    "oakd.launch.py"
                ])
            ),
            launch_arguments={
                "pointcloud": LaunchConfiguration("pointcloud"),
            }.items()
        )
        actions.append(oakd_launch)

    return actions


def generate_launch_description():
    """Declare launch arguments and include pt_control's and pt_bringup's own launch files."""
    declared_arguments = [
        DeclareLaunchArgument(
            "sts_serial_port",
            default_value="",
            description="Serial port override; empty string means use urdf_config.yaml value",
        ),
        DeclareLaunchArgument(
            "use_mock",
            default_value="",
            description="Mock mode override (true/false); empty string means use urdf_config.yaml value",
        ),
        DeclareLaunchArgument(
            "diagnostics",
            default_value="true",
            description="Launch motor diagnostics node",
        ),
        DeclareLaunchArgument(
            "pantilt_config",
            default_value="pt101",
            description='Pan-tilt mesh variant: "pt100" or "pt101" (pt101 is recommended and default)',
        ),
        DeclareLaunchArgument(
            "pointcloud",
            default_value="false",
            description="Enable RGBD point cloud pipeline.",
        ),
        DeclareLaunchArgument(
            "use_sim_time",
            default_value="false",
            description="Use /clock from a simulator instead of system time.",
        ),
        DeclareLaunchArgument(
            "sim",
            default_value="false",
            description="Run against Gazebo instead of real hardware: starts gz_sim, uses "
                        "gz_ros2_control for the pan-tilt mechanism, forces use_sim_time/use_mock, "
                        "and skips oakd (no simulated equivalent yet).",
        ),
        DeclareLaunchArgument(
            "gui",
            default_value="true",
            description="[sim only] Launch Gazebo with the GUI client attached.",
        ),
    ]

    return LaunchDescription(declared_arguments + [OpaqueFunction(function=launch_setup)])
