#!/usr/bin/env python3
"""
Main bringup launch file for the Pan Tilt 100 system.

This launch file includes pt_control's pantilt.launch.py (robot control stack) and
forwards relevant launch arguments to it. No camera driver is included - the OAK-D S2
is represented in the URDF as a mesh/link/fixed-joint only (see pt_description), not
a live sensor.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def launch_setup(context):
    """Include pt_control's control stack."""
    pt_control_args = {
        "sts_serial_port": LaunchConfiguration("sts_serial_port"),
        "use_mock": LaunchConfiguration("use_mock"),
        "diagnostics": LaunchConfiguration("diagnostics"),
        "pantilt_config": LaunchConfiguration("pantilt_config"),
        "use_sim_time": LaunchConfiguration("use_sim_time"),
    }

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

    return [pantilt_control_launch]


def generate_launch_description():
    """Declare launch arguments and include pt_control's pantilt.launch.py."""
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
            "use_sim_time",
            default_value="false",
            description="Use /clock from a simulator instead of system time.",
        ),
    ]

    return LaunchDescription(declared_arguments + [OpaqueFunction(function=launch_setup)])
