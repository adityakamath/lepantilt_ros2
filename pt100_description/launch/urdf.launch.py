#!/usr/bin/env python3
"""
Pan Tilt 100 Visualization Launch File

This launch file starts only robot_state_publisher for visualization or URDF manipulation
"""

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import Command, FindExecutable, PathJoinSubstitution
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    """
    Generate a minimal launch description for Pan-Tilt100 visualization.
    Starts only robot_state_publisher with the URDF generated from xacro.
    No hardware or controllers are launched.
    """


    # Generate robot_description from xacro (expands the URDF at launch time)
    robot_description_content = Command([
        PathJoinSubstitution([FindExecutable(name="xacro")]),
        " ",
        PathJoinSubstitution([
            FindPackageShare("pt100_description"),
            "urdf",
            "pantilt.urdf.xacro",
        ])
    ])
    robot_description = {
        "robot_description": ParameterValue(robot_description_content, value_type=str)
    }

    # Start only robot_state_publisher to publish TFs and joint states from the URDF
    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="log",
        parameters=[robot_description],
        name="robot_state_publisher",
        emulate_tty=True,
        arguments=["--ros-args", "--log-level", "WARN"],
    )

    # Return the launch description with only the state publisher node
    return LaunchDescription([robot_state_publisher_node])
