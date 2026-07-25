#!/usr/bin/env python3
"""
Main bringup launch file for the complete Pan Tilt 100 system: mechanism + camera.

This launch file includes:
    - pt_control's pantilt.launch.py (robot control stack)
    - pt_bringup's oakd.launch.py (OAK-D camera) - real hardware only; sim:=true (MuJoCo)
      skips it, mujoco_ros2_control's own ros2_control_node is self-contained
It forwards relevant launch arguments to each included launch file.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def launch_setup(context):
    """Include pt_control's control stack, plus either oakd (real) or nothing more (sim - MuJoCo is self-contained)."""
    use_mock     = LaunchConfiguration("use_mock").perform(context)
    sim          = LaunchConfiguration("sim").perform(context).strip().lower() in ("true", "1")
    gui          = LaunchConfiguration("gui").perform(context)
    use_sim_time = LaunchConfiguration("use_sim_time").perform(context)

    if sim:
        # Running in sim implies sim time; keep any explicit use_mock override, otherwise
        # force it so the STS plugin (unused in sim, but still resolved by xacro defaults)
        # never assumes a real serial port is present.
        use_sim_time = "true"
        use_mock = use_mock or "true"

    hw_type = "mujoco" if sim else "real"

    pt_control_args = {
        "sts_serial_port": LaunchConfiguration("sts_serial_port"),
        "use_mock": use_mock,
        "diagnostics": LaunchConfiguration("diagnostics"),
        "pantilt_config": LaunchConfiguration("pantilt_config"),
        "use_sim_time": use_sim_time,
        "ros2_control_hardware_type": hw_type,
    }
    if hw_type == "mujoco":
        pt_control_args["mujoco_headless"] = "false" if gui.lower() in ("true", "1") else "true"

    pantilt_control_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare("pt_control"),
                "launch",
                "pantilt.launch.py"
            ])
        ),
        launch_arguments=pt_control_args.items()
    )

    actions = [pantilt_control_launch]

    if hw_type == "real":
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
    # hw_type == "mujoco": nothing more to start - mujoco_ros2_control's own
    # ros2_control_node (started by pt_control/launch/pantilt.launch.py above) hosts the
    # MuJoCo simulation itself, no separate simulator process, bridge, or entity spawn needed.

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
            description="Run against MuJoCo instead of real hardware: forces use_sim_time/use_mock, "
                        "and skips oakd (no simulated equivalent yet).",
        ),
        DeclareLaunchArgument(
            "gui",
            default_value="true",
            description="[sim only] Launch with the MuJoCo Simulate viewer attached.",
        ),
    ]

    return LaunchDescription(declared_arguments + [OpaqueFunction(function=launch_setup)])
