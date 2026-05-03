from launch import LaunchDescription
from launch.actions import ExecuteProcess

def generate_launch_description():

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
        joint_state_broadcaster,
        steering_controller,
        rear_wheel_controller,
    ])