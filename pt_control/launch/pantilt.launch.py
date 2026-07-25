#!/usr/bin/env python3
"""
Pan Tilt 100 ROS 2 control stack launch file.

This launch file starts:
    - robot_state_publisher
    - controller_manager (ros2_control) - real mode uses the standard controller_manager
      node; mujoco mode uses a modified ros2_control_node from the mujoco_ros2_control
      package itself, which also hosts the MuJoCo simulation in-process
    - joint_state_broadcaster
    - pantilt_controller
    - (optionally) motor diagnostics
    - joystick teleop
Hardware parameters are read from urdf_config.yaml; sts_serial_port and
use_mock can be overridden on the command line (empty string = use yaml value).
"""

import subprocess
import tempfile

import yaml

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription, OpaqueFunction, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node, SetRemap
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def launch_setup(context):
    """Build the PT100 control-stack nodes, reading urdf_config.yaml for xacro args."""
    serial_port    = LaunchConfiguration('sts_serial_port').perform(context)
    use_mock       = LaunchConfiguration('use_mock').perform(context)
    diagnostics    = LaunchConfiguration('diagnostics').perform(context)
    pantilt_config = LaunchConfiguration('pantilt_config').perform(context)
    use_sim_time   = LaunchConfiguration('use_sim_time').perform(context).lower() in ('true', '1')
    hw_type = LaunchConfiguration('ros2_control_hardware_type').perform(context)
    mujoco_model    = LaunchConfiguration('mujoco_model').perform(context)
    mujoco_headless = LaunchConfiguration('mujoco_headless').perform(context)

    pkg_ctrl = FindPackageShare('pt_control').perform(context)
    pkg_desc = FindPackageShare('pt_description').perform(context)
    xacro    = FindExecutable(name='xacro').perform(context)

    # MJCF must be xacro-processed here (unlike robot_description below, it has to land on
    # disk since MJCF's <include> is filesystem-path-based, not an in-memory param string).
    # Same pantilt_config arg picks both the URDF and MJCF mesh variant.
    if mujoco_model:
        final_mujoco_model = mujoco_model
    elif hw_type == 'mujoco':
        mjcf_xml = subprocess.run(
            [xacro, f'{pkg_desc}/mjcf/pantilt.mjcf.xacro', f'pantilt_config:={pantilt_config}'],
            capture_output=True, text=True, check=True,
        ).stdout
        mjcf_file = tempfile.NamedTemporaryFile(
            mode='w', suffix='.xml', prefix='pantilt_mujoco_', delete=False)
        mjcf_file.write(mjcf_xml)
        mjcf_file.close()
        final_mujoco_model = mjcf_file.name
    else:
        final_mujoco_model = ''

    _cfg = yaml.safe_load(open(f'{pkg_ctrl}/config/urdf_config.yaml'))
    final_serial_port = serial_port if serial_port else _cfg['serial_port']
    final_use_mock    = use_mock if use_mock else str(_cfg['use_mock']).lower()

    xacro_cmd = (
        f'{xacro} {pkg_desc}/urdf/pantilt.urdf.xacro'
        f' serial_port:={final_serial_port}'
        f' use_mock:={final_use_mock}'
        f' baud_rate:={_cfg["baud_rate"]}'
        f' use_sync_write:={str(_cfg["use_sync_write"]).lower()}'
        f' pantilt_config:={pantilt_config}'
        f' pan_motor_id:={_cfg["pan_motor_id"]}'
        f' tilt_motor_id:={_cfg["tilt_motor_id"]}'
        f' pan_center_steps:={_cfg["pan_center_steps"]}'
        f' tilt_center_steps:={_cfg["tilt_center_steps"]}'
        f' sts_max_velocity_steps:={_cfg["sts_max_velocity_steps"]}'
        f' proportional_vel_max:={_cfg["proportional_vel_max"]}'
        f' pan_joint_lower:={_cfg["pan_joint_lower"]}'
        f' pan_joint_upper:={_cfg["pan_joint_upper"]}'
        f' tilt_joint_lower:={_cfg["tilt_joint_lower"]}'
        f' tilt_joint_upper:={_cfg["tilt_joint_upper"]}'
    )
    if hw_type == 'mujoco':
        xacro_cmd += (
            f' ros2_control_hardware_type:={hw_type}'
            f' mujoco_model:={final_mujoco_model}'
            f' mujoco_headless:={mujoco_headless}'
        )

    robot_description = {
        'robot_description': ParameterValue(Command([xacro_cmd]), value_type=str)
    }

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='log',
        parameters=[robot_description, {'use_sim_time': use_sim_time}],
        name='robot_state_publisher',
        emulate_tty=True,
        arguments=['--ros-args', '--log-level', 'WARN'],
    )

    controller_manager = Node(
        package='controller_manager',
        executable='ros2_control_node',
        parameters=[robot_description, f'{pkg_ctrl}/config/pantilt_config.yaml', {'use_sim_time': use_sim_time}],
        remappings=[('/diagnostics', '/controller_manager/diagnostics')],
        output='log',
        emulate_tty=True,
        arguments=['--ros-args', '--log-level', 'rclcpp:=ERROR'],
    )

    # mujoco_ros2_control ships its own ros2_control_node, hosting the MuJoCo simulation
    # itself - use_sim_time:true is required regardless of the launch arg. The
    # mujoco_ros2_control_plugins.yaml CameraPlugin config isn't loaded here yet - the apt
    # package (0.0.3) doesn't ship CameraPlugin, and loading a nonexistent plugin class is a
    # fatal error, not a skip. See README's "Camera (oak_rgb)" section.
    mujoco_control_node = Node(
        package='mujoco_ros2_control',
        executable='ros2_control_node',
        parameters=[
            robot_description,
            f'{pkg_ctrl}/config/pantilt_config.yaml',
            {'use_sim_time': True},
        ],
        remappings=[('/diagnostics', '/controller_manager/diagnostics')],
        output='both',
    )

    teleop_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([FindPackageShare('pt_control'), 'launch', 'teleop.launch.py'])
        ]),
        launch_arguments={'use_sim_time': str(use_sim_time).lower()}.items(),
    )

    motor_diagnostics = GroupAction([
        SetRemap('/diagnostics', '/base/diagnostics'),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                PathJoinSubstitution([FindPackageShare('sts_hardware_interface'), 'launch', 'motor_diagnostics.launch.py'])
            ])
        ),
    ])

    control_node_actions = [mujoco_control_node] if hw_type == 'mujoco' else [controller_manager]

    actions = [
        robot_state_publisher,
        *control_node_actions,
        TimerAction(period=2.0, actions=[Node(
            package='controller_manager', executable='spawner',
            arguments=['joint_state_broadcaster', '-c', '/controller_manager',
                       '--controller-manager-timeout', '30'], output='both',
        )]),
        TimerAction(period=2.5, actions=[Node(
            package='controller_manager', executable='spawner',
            arguments=['pantilt_controller', '-c', '/controller_manager',
                       '--controller-manager-timeout', '30'], output='both',
        )]),
        teleop_launch,
    ]

    if diagnostics.lower() == 'true':
        actions.append(TimerAction(period=3.0, actions=[motor_diagnostics]))

    return actions


def generate_launch_description():
    """Declare control-stack launch arguments and launch via launch_setup."""
    declared_arguments = [
        DeclareLaunchArgument(
            'sts_serial_port',
            default_value='',
            description='Serial port override; empty string means use urdf_config.yaml value',
        ),
        DeclareLaunchArgument(
            'use_mock',
            default_value='',
            description='Mock mode override (true/false); empty string means use urdf_config.yaml value',
        ),
        DeclareLaunchArgument(
            'diagnostics',
            default_value='true',
            description='Launch motor diagnostics node',
        ),
        DeclareLaunchArgument(
            'pantilt_config',
            default_value='pt101',
            description='Pan-tilt mesh variant: "pt100" or "pt101" (pt101 is recommended and default)',
        ),
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use /clock from a simulator instead of system time.',
        ),
        DeclareLaunchArgument(
            'ros2_control_hardware_type',
            default_value='real',
            description='"real" for the STS hardware plugin, "mujoco" for '
                        'mujoco_ros2_control/MujocoSystemInterface. ("gazebo" is also supported at the '
                        'URDF/xacro level - pantilt.control.xacro/pantilt.urdf.xacro - but not wired into '
                        'this launch file.)',
        ),
        DeclareLaunchArgument(
            'mujoco_model',
            default_value='',
            description='Path to a pre-built MJCF file to load; empty means xacro-process '
                        'pt_description/mjcf/pantilt.mjcf.xacro with pantilt_config at launch '
                        'time instead (so pantilt_config alone picks the pt100/pt101 MJCF too). Only '
                        'used when ros2_control_hardware_type:="mujoco".',
        ),
        DeclareLaunchArgument(
            'mujoco_headless',
            default_value='false',
            description='[mujoco only] Run without the MuJoCo Simulate viewer window.',
        ),
    ]

    return LaunchDescription(declared_arguments + [OpaqueFunction(function=launch_setup)])
