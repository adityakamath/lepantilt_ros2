#!/usr/bin/env python3
"""
Pan Tilt 100 ROS 2 control stack launch file.

This launch file starts:
    - robot_state_publisher
    - controller_manager (ros2_control)
    - joint_state_broadcaster
    - pantilt_controller
    - (optionally) motor diagnostics
    - (optionally) joystick teleop
Arguments are provided for hardware configuration and diagnostics.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, FindExecutable, PathJoinSubstitution, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    """
    Generate launch description for Pan-Tilt100 control stack.
    Declares arguments for hardware, diagnostics, and launches nodes in sequence.
    """

    # Declare launch arguments for hardware and diagnostics
    declared_arguments = [
        DeclareLaunchArgument(
            "serial_port",
            default_value="/dev/ttySERVO",
            description="Serial port for STS motor communication",
        ),
        DeclareLaunchArgument(
            "use_mock",
            default_value="false",
            description="Use mock/simulation mode (no hardware required)",
        ),
        DeclareLaunchArgument(
            "use_sync_write",
            default_value="true",
            description="Enable SyncWrite for coordinated motion",
        ),
        DeclareLaunchArgument(
            "diagnostics",
            default_value="true",
            description="Launch motor diagnostics node (if true)",
        ),
        DeclareLaunchArgument(
            "pan_center_steps",
            default_value="2048",
            description="Raw step value (0-4095) that maps to 0 rad on pan axis",
        ),
        DeclareLaunchArgument(
            "tilt_center_steps",
            default_value="2646",
            description="Raw step value (0-4095) that maps to 0 rad on tilt axis",
        ),
    ]

    # Generate robot_description from xacro
    robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            PathJoinSubstitution([
                FindPackageShare("pt100_description"),
                "urdf",
                "pantilt.urdf.xacro",
            ]),
            " ",
            "serial_port:=",
            LaunchConfiguration("serial_port"),
            " ",
            "use_mock:=",
            LaunchConfiguration("use_mock"),
            " ",
            "use_sync_write:=",
            LaunchConfiguration("use_sync_write"),
            " ",
            "pan_center_steps:=",
            LaunchConfiguration("pan_center_steps"),
            " ",
            "tilt_center_steps:=",
            LaunchConfiguration("tilt_center_steps"),
        ]
    )
    robot_description = {
        "robot_description": ParameterValue(robot_description_content, value_type=str)
    }

    controller_config = PathJoinSubstitution(
        [FindPackageShare("pt100_control"), "config", "pantilt_control_config.yaml"]
    )

    # Publishes robot state (TFs, joint states)
    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="log",
        parameters=[robot_description],
        name="robot_state_publisher",
        emulate_tty=True,
        arguments=["--ros-args", "--log-level", "WARN"],
    )

    # Main ros2_control node
    controller_manager_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[robot_description, controller_config],
        output="log",
        emulate_tty=True,
    )

    # Spawns joint_state_broadcaster controller
    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", "-c", "/controller_manager"],
        output="both",
    )

    # Spawns pantilt_controller
    pantilt_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["pantilt_controller", "-c", "/controller_manager"],
        output="both",
    )

    # Optionally include diagnostics launch file
    diagnostics_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                PathJoinSubstitution([
                    FindPackageShare("sts_hardware_interface"),
                    "launch",
                    "motor_diagnostics.launch.py",
                ])
            ]
        )
    )

    # Optionally include joystick teleop launch file
    teleop_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                PathJoinSubstitution([
                    FindPackageShare("pt100_control"),
                    "launch",
                    "teleop.launch.py",
                ])
            ]
        )
    )

    # Delay controller spawners and diagnostics for proper startup sequence
    delayed_joint_state_broadcaster_spawner = TimerAction(
        period=2.0,
        actions=[joint_state_broadcaster_spawner],
    )

    delayed_pantilt_controller_spawner = TimerAction(
        period=2.5,
        actions=[pantilt_controller_spawner],
    )

    delayed_diagnostics_launch = TimerAction(
        period=3.0,
        actions=[diagnostics_launch],
        condition=IfCondition(LaunchConfiguration('diagnostics')),
    )

    # Compose and return the launch description
    return LaunchDescription(declared_arguments + [
        robot_state_publisher_node,
        controller_manager_node,
        delayed_joint_state_broadcaster_spawner,
        delayed_pantilt_controller_spawner,
        delayed_diagnostics_launch,
        teleop_launch,
    ])
