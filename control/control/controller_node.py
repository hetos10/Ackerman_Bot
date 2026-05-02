#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Point
from geometry_msgs.msg import Twist


class ControllerNode(Node):

    def __init__(self):

        super().__init__('controller_node')

        # Subscribe target info
        self.target_subscriber = self.create_subscription(
            Point,
            '/target_info',
            self.target_callback,
            10
        )

        # Publish velocity commands
        self.cmd_publisher = self.create_publisher(
            Twist,
            '/cmd_vel',
            10
        )

        # Image center
        self.image_width = 640
        self.image_center_x = self.image_width / 2

        # Control gain
        self.kp_steering = 0.003

        # Stop threshold
        self.target_area_threshold = 50000

        self.get_logger().info("Controller Node Started")


    def target_callback(self, msg):

        cmd = Twist()

        # No target detected
        if msg.x == -1.0:

            cmd.linear.x = 0.0
            cmd.angular.z = 0.0

            self.cmd_publisher.publish(cmd)

            self.get_logger().info("Searching for target...")

            return

        # Compute image error
        error_x = msg.x - self.image_center_x

        # Steering control
        steering_command = -self.kp_steering * error_x

        # Limit steering
        steering_command = max(min(steering_command, 0.5), -0.5)

        # Forward speed
        forward_speed = 0.5

        # Stop if close enough
        if msg.z > self.target_area_threshold:

            forward_speed = 0.0
            steering_command = 0.0

            self.get_logger().info("Reached Target")

        # Ackerman-like behavior
        # Always move forward while steering

        cmd.linear.x = forward_speed
        cmd.angular.z = steering_command

        self.cmd_publisher.publish(cmd)

        self.get_logger().info(
            f"Error: {error_x:.2f}, Steering: {steering_command:.2f}"
        )


def main(args=None):

    rclpy.init(args=args)

    node = ControllerNode()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()