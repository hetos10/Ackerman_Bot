#!/usr/bin/env python3

import rclpy
import numpy as np

from rclpy.node import Node

from geometry_msgs.msg import Point
from std_msgs.msg import Float64MultiArray


class SimpleControllerNode(Node):

    def __init__(self):

        super().__init__('controller_node')

        self.target_subscriber = self.create_subscription(
            Point,
            '/target_info',
            self.target_callback,
            10
        )

        self.steering_pub = self.create_publisher(
            Float64MultiArray,
            '/steering_controller/commands',
            10
        )

        self.throttle_pub = self.create_publisher(
            Float64MultiArray,
            '/rear_wheel_controller/commands',
            10
        )

        self.image_center_x = 320.0

        self.kp_steering = 0.0025

        self.max_steering = 0.45

        self.max_speed = 5.0

        self.stop_area_threshold = 42000.0

        self.min_detect_area = 1000.0

        self.search_speed = 1.5

        self.search_steering = 0.25

        self.get_logger().info("Controller Node Started")


    def publish_commands(self, steering, velocity):

        steering_msg = Float64MultiArray()
        throttle_msg = Float64MultiArray()

        steering_msg.data = [float(steering)]

        throttle_msg.data = [
            float(velocity),
            float(velocity)
        ]

        self.steering_pub.publish(steering_msg)
        self.throttle_pub.publish(throttle_msg)


    def stop_robot(self):

        self.publish_commands(0.0, 0.0)


    def target_callback(self, msg):

        target_x = msg.x
        target_y = msg.y
        target_area = msg.z

        if target_area < self.min_detect_area:

            self.get_logger().info("Searching for Target")

            self.publish_commands(
                self.search_steering,
                self.search_speed
            )

            return

        error = target_x - self.image_center_x

        steering = -self.kp_steering * error

        steering = np.clip(
            steering,
            -self.max_steering,
            self.max_steering
        )

        if target_area >= self.stop_area_threshold:

            self.get_logger().info("Target Reached")

            self.stop_robot()

            return

        speed_scale = 1.0 - (
            target_area / self.stop_area_threshold
        )

        speed_scale = np.clip(
            speed_scale,
            0.2,
            1.0
        )

        velocity = self.max_speed * speed_scale

        self.publish_commands(
            steering,
            velocity
        )

        self.get_logger().info(
            f'Error: {error:.2f} | '
            f'Area: {target_area:.2f} | '
            f'Steering: {steering:.2f} | '
            f'Velocity: {velocity:.2f}'
        )


def main(args=None):

    rclpy.init(args=args)

    node = SimpleControllerNode()

    try:

        rclpy.spin(node)

    except KeyboardInterrupt:

        pass

    finally:

        node.stop_robot()

        node.destroy_node()

        rclpy.shutdown()


if __name__ == '__main__':

    main()