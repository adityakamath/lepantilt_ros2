#!/usr/bin/env python3
"""
Launch the lepantilt ros2_control stack with standard controllers.

Starts robot_state_publisher, controller_manager, joint_state_broadcaster, lepantilt_controller,
motor diagnostics, and optionally joystick teleop.
"""

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    TimerAction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    Command,
    FindExecutable,
    PathJoinSubstitution,
    LaunchConfiguration,
)
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    declared_arguments = []

    declared_arguments.append(
        DeclareLaunchArgument(
            "serial_port",
            default_value="/dev/ttySERVO",
            description="Serial port for STS motor communication",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "use_mock",
            default_value="false",
            description="Use mock/simulation mode (no hardware required)",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "use_sync_write",
            default_value="true",
            description="Enable SyncWrite for coordinated motion",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "tilt",
            default_value="s2",
            description="Tilt link mesh variant: s2 or lite",
        )
    )
    serial_port = LaunchConfiguration("serial_port")
    use_mock = LaunchConfiguration("use_mock")
    use_sync_write = LaunchConfiguration("use_sync_write")
    tilt = LaunchConfiguration("tilt")

    robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            PathJoinSubstitution(
                [
                    FindPackageShare("lepantilt_description"),
                    "urdf",
                    "pantilt.urdf.xacro",
                ]
            ),
            " ",
            "serial_port:=",
            serial_port,
            " ",
            "use_mock:=",
            use_mock,
            " ",
            "use_sync_write:=",
            use_sync_write,
            " ",
            "tilt:=",
            tilt,
        ]
    )
    robot_description = {
        "robot_description": ParameterValue(robot_description_content, value_type=str)
    }

    controller_config = PathJoinSubstitution(
        [FindPackageShare("lepantilt_control"), "config", "lepantilt_controllers.yaml"]
    )

    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="log",
        parameters=[robot_description],
        name="robot_state_publisher",
        emulate_tty=True,
        arguments=["--ros-args", "--log-level", "WARN"],
    )

    controller_manager_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[robot_description, controller_config],
        output="log",
        emulate_tty=True,
        name="controller_manager",
    )

    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", "-c", "/controller_manager"],
        output="both",
    )

    lepantilt_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["lepantilt_controller", "-c", "/controller_manager"],
        output="both",
    )

    diagnostics_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                PathJoinSubstitution(
                    [
                        FindPackageShare("sts_hardware_interface"),
                        "launch",
                        "motor_diagnostics.launch.py",
                    ]
                )
            ]
        )
    )

    joy_teleop_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                PathJoinSubstitution(
                    [
                        FindPackageShare("lepantilt_control"),
                        "launch",
                        "joy_teleop.launch.py",
                    ]
                )
            ]
        )
    )

    return LaunchDescription(
        [
            *declared_arguments,
            robot_state_publisher_node,
            controller_manager_node,
            TimerAction(period=2.0, actions=[joint_state_broadcaster_spawner]),
            TimerAction(period=2.5, actions=[lepantilt_controller_spawner]),
            TimerAction(period=3.0, actions=[diagnostics_launch]),
            joy_teleop_launch,
        ]
    )
