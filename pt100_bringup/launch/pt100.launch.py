#!/usr/bin/env python3
"""
Main bringup launch file for the Pan-Tilt100 robot.

This launch file includes:
    - pt100_control's pantilt.launch.py (robot control stack)
    - pt100_bringup's oakd.launch.py (OAK-D camera)
It forwards relevant launch arguments to each included launch file.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    """
    Generate a launch description that brings up the PanTilt robot control and camera nodes.
    Declares and forwards arguments to included launch files.
    """

    # Declare launch arguments for bringup
    declared_arguments = [
        DeclareLaunchArgument(
            "use_mock",
            default_value="false",
            description="Use mock/simulation mode (no hardware required)",
        ),
        DeclareLaunchArgument(
            "diagnostics",
            default_value="true",
            description="Launch motor diagnostics node",
        ),
        DeclareLaunchArgument(
            "pointcloud",
            default_value="false",
            description="Enable RGBD point cloud pipeline.",
        ),
    ]

    # Include the PanTilt control stack launch file, forwarding use_mock and diagnostics
    pt100_control_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare("pt100_control"),
                "launch",
                "pantilt.launch.py"
            ])
        ),
        launch_arguments={
            "use_mock": LaunchConfiguration("use_mock"),
            "diagnostics": LaunchConfiguration("diagnostics"),
        }.items()
    )

    # Include the OAK-D camera launch file, forwarding params_file
    oakd_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare("pt100_bringup"),
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
        pt100_control_launch,
        oakd_launch
    ])
