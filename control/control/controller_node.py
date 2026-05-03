#!/usr/bin/env python3
"""
Simple Controller Node
- Takes target position from vision node
- Publishes steering and throttle commands
- Uses simple proportional control
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point
from std_msgs.msg import Float32
import math


class SimpleControllerNode(Node):

    def __init__(self):
        super().__init__('controller_node')
        
        # Subscribe to target info
        self.target_subscriber = self.create_subscription(
            Point,
            '/target_info',
            self.target_callback,
            10
        )
        
        # Publish steering and throttle
        self.steering_pub = self.create_publisher(Float32, '/steering_controller/commands', 10)
        self.throttle_pub = self.create_publisher(Float32, '/rear_wheel_controller/commands', 10)
        
        # Robot parameters
        self.wheelbase = 0.29502
        self.max_steering = 0.524  # ~30 degrees
        self.image_center_x = 320  # Half of 640
        
        # Control gains
        self.kp = 1.5  # Steering gain
        
        self.get_logger().info("Simple Controller Node Started")


    def target_callback(self, msg):
        """Receive target position and publish control commands"""
        
        # If no target found
        if msg.x < 0:
            steering = 0.0
            throttle = 0.0
        else:
            # Calculate lateral error
            error = msg.x - self.image_center_x
            
            # Steering control (proportional)
            steering = self.kp * error / self.image_center_x
            
            # Clamp steering
            steering = max(-self.max_steering, min(self.max_steering, steering))
            
            # Forward speed
            throttle = 0.5
            
            # Stop if close
            if msg.z > 40000:  # Close to camera
                throttle = 0.0
                steering = 0.0
        
        # Publish commands
        steering_msg = Float32(data=float(steering))
        throttle_msg = Float32(data=float(throttle))
        
        self.steering_pub.publish(steering_msg)
        self.throttle_pub.publish(throttle_msg)
        
        if msg.x >= 0:
            self.get_logger().info(f"Steering: {steering:.3f}, Throttle: {throttle:.3f}")


def main(args=None):
    rclpy.init(args=args)
    node = SimpleControllerNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()