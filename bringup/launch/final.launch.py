import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, ExecuteProcess, DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():

    world_name = LaunchConfiguration("world_name")

    world_name_arg = DeclareLaunchArgument(
        "world_name",
        default_value="shapes.sdf"
    )

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("description"),
                "launch",
                "gazebo.launch.py"
            )
        ),
        launch_arguments={
            "world_name": world_name
        }.items()
    )

    rviz = Node(
        package="rviz2",
        executable="rviz2",
        arguments=[
            "-d",
            os.path.join(
                get_package_share_directory("description"),
                "rviz",
                "display.rviz"
            )
        ],
        output="screen",
        parameters=[{"use_sim_time": True}],
    )

    perception_node = Node(
        package="control",
        executable="perception_node",
        name="perception_node",
        output="screen",
        parameters=[{"use_sim_time": True}]
    )

    controller_node = Node(
        package="control",
        executable="controller_node",
        name="controller_node",
        output="screen",
        parameters=[{"use_sim_time": True}]
    )

    bridge_node = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            "--ros-args",
            "-p",
            f'config_file:={os.path.join(get_package_share_directory("bringup"),"config","bridge.yaml")}'
        ],
        output="screen"
    )

    joint_state_broadcaster = ExecuteProcess(
        cmd=[
            "ros2",
            "control",
            "load_controller",
            "--set-state",
            "active",
            "joint_state_broadcaster"
        ],
        output="screen"
    )

    steering_controller = ExecuteProcess(
        cmd=[
            "ros2",
            "control",
            "load_controller",
            "--set-state",
            "active",
            "steering_controller"
        ],
        output="screen"
    )

    rear_wheel_controller = ExecuteProcess(
        cmd=[
            "ros2",
            "control",
            "load_controller",
            "--set-state",
            "active",
            "rear_wheel_controller"
        ],
        output="screen"
    )

    return LaunchDescription([
        world_name_arg,
        gazebo,
        bridge_node,
        joint_state_broadcaster,
        steering_controller,
        rear_wheel_controller,
        perception_node,
        controller_node,
        rviz,
    ])