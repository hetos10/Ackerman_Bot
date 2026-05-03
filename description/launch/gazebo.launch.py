import os
from os import pathsep
from pathlib import Path
from ament_index_python.packages import get_package_share_directory
import xacro

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution, PythonExpression
from launch.launch_description_sources import PythonLaunchDescriptionSource

from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():

    world_name = LaunchConfiguration("world_name")

    world_name_arg = DeclareLaunchArgument(
        "world_name",
        default_value="shapes"
    )

    description_pkg = get_package_share_directory("description")

    world_path = PathJoinSubstitution([
            description_pkg,
            "worlds",
            PythonExpression(expression=["'", LaunchConfiguration("world_name"), "'", " + '.sdf'"])
        ]
    )

    xacro_file = os.path.join(
        description_pkg,
        "urdf",
        "ack.urdf.xacro"
    )

    robot_description_config = xacro.process_file(xacro_file)

    robot_description = {
        "robot_description": robot_description_config.toxml()
    }

    bridge_file = os.path.join(
        get_package_share_directory("description"),
        "config",
        "bridge.yaml"
    )

    gazebo = IncludeLaunchDescription(
                PythonLaunchDescriptionSource([os.path.join(
                    get_package_share_directory("ros_gz_sim"), "launch"), "/gz_sim.launch.py"]),
                launch_arguments={
                    "gz_args": PythonExpression(["'", world_path, " -v 4 -r'"])
                }.items()
             )

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        parameters=[robot_description, {"use_sim_time": True}],
        output="screen"
    )

    spawn_robot = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-topic",
            "robot_description",
            "-name",
            "ackerman_robot",
            "-x",
            "0.0",
            "-y",
            "0.0",
            "-z",
            "0.5"
        ],
        output="screen"
    )

    bridge_node = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            "--ros-args",
            "-p",
            f"config_file:={bridge_file}"
        ],
        output="screen"
    )

    return LaunchDescription([
        world_name_arg,
        gazebo,
        robot_state_publisher,
        spawn_robot,
        bridge_node,
    ])