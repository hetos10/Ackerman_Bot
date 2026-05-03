import os

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument

from launch.substitutions import LaunchConfiguration

from launch.launch_description_sources import PythonLaunchDescriptionSource

from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    world_name = LaunchConfiguration("world_name")

    world_name_arg = DeclareLaunchArgument(
        "world_name",
        default_value="shapes"
    )

    gazebo_launch = IncludeLaunchDescription(
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

    display_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("description"),
                "launch",
                "display.launch.py"
            )
        )
    )

    controllers_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("description"),
                "launch",
                "ros2_controllers.launch.py"
            )
        )
    )

    control_nodes_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("control"),
                "launch",
                "control.launch.py"
            )
        )
    )

    return LaunchDescription([
        world_name_arg,
        gazebo_launch,
        display_launch,
        controllers_launch,
        # control_nodes_launch,
    ])