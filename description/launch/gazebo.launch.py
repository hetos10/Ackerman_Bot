import os
import xacro

from launch import LaunchDescription
from launch.actions import ExecuteProcess, DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

from ament_index_python.packages import get_package_share_directory

def generate_launch_description():

    world_name = LaunchConfiguration("world_name")

    world_name_arg = DeclareLaunchArgument(
        "world_name",
        default_value="shapes.sdf"
    )

    description_pkg = get_package_share_directory("description")

    world_file = os.path.join(
        description_pkg,
        "worlds",
        world_name.perform({})
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
        get_package_share_directory("bringup"),
        "config",
        "bridge.yaml"
    )

    gazebo = ExecuteProcess(
        cmd=[
            "gz",
            "sim",
            "-r",
            world_file
        ],
        output="screen"
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