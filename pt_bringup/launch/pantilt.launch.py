#!/usr/bin/env python3
"""
Main bringup launch file for the complete Pan Tilt 100 system: mechanism + camera.

This launch file includes:
    - pt_control's pantilt.launch.py (robot control stack)
    - pt_bringup's oakd.launch.py (OAK-D camera)
It forwards relevant launch arguments to each included launch file.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    """
    Generate a launch description that brings up the Pan Tilt 100 mechanism control and camera nodes.
    Declares and forwards arguments to included launch files.
    """

    # Declare launch arguments for bringup
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
    ]

    # Include the PanTilt control stack launch file, forwarding use_mock and diagnostics
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
            "use_mock": LaunchConfiguration("use_mock"),
            "diagnostics": LaunchConfiguration("diagnostics"),
            "pantilt_config": LaunchConfiguration("pantilt_config"),
            "use_sim_time": LaunchConfiguration("use_sim_time"),
        }.items()
    )

    # Include the OAK-D camera launch file, forwarding params_file
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

    # Return the composed launch description
    return LaunchDescription(declared_arguments + [
        pantilt_control_launch,
        oakd_launch
    ])
