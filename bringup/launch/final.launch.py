import os

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument

from launch.substitutions import LaunchConfiguration

from launch.launch_description_sources import PythonLaunchDescriptionSource

from launch_ros.actions import Node

from ament_index_python.packages import get_package_share_directory

def generate_launch_description():

    world_name = LaunchConfiguration("world_name")

    world_name_arg = DeclareLaunchArgument(
        "world_name",
        default_value="shapes.sdf"
    )

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("bringup"),
                "launch",
                "gazebo.launch.py"
            )
        ),
        launch_arguments={
            "world_name": world_name
        }.items()
    )

    controllers = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("bringup"),
                "launch",
                "controllers.launch.py"
            )
        )
    )

    control_nodes = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("control"),
                "launch",
                "control.launch.py"
            )
        )
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

    return LaunchDescription([
        world_name_arg,
        gazebo,
        controllers,
        control_nodes,
        rviz,
    ])