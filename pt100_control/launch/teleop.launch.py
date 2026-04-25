#!/usr/bin/env python3
"""
Launch joy_teleop for Pan-Tilt100 joystick control.

Subscribes to /joy and publishes JointTrajectory commands to pt100_controller.
"""

from launch import LaunchDescription
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    teleop_config = PathJoinSubstitution(
        [FindPackageShare("pt100_control"), "config", "teleop_config.yaml"]
    )

    teleop_node = Node(
        package="joy_teleop",
        executable="joy_teleop",
        name="joy_teleop",
        output="log",
        parameters=[teleop_config],
    )

    return LaunchDescription([teleop_node])
