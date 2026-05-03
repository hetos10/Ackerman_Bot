from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():

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

    return LaunchDescription([
        perception_node,
        controller_node,
    ])