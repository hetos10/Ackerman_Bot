#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Image
from geometry_msgs.msg import Point

from cv_bridge import CvBridge

import cv2
import numpy as np


class PerceptionNode(Node):

    def __init__(self):

        super().__init__('perception_node')

        self.bridge = CvBridge()

        # Subscribe to camera feed
        self.image_subscriber = self.create_subscription(
            Image,
            '/camera/image_raw',
            self.image_callback,
            10
        )

        # Publish target information
        self.target_publisher = self.create_publisher(
            Point,
            '/target_info',
            10
        )

        self.get_logger().info("Perception Node Started")


    def image_callback(self, msg):

        # Convert ROS image to OpenCV image
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')

        # Resize (optional)
        frame = cv2.resize(frame, (640, 480))

        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Blur image
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Edge detection
        edges = cv2.Canny(blurred, 50, 150)

        # Find contours
        contours, _ = cv2.findContours(
            edges,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        target_found = False

        for contour in contours:

            area = cv2.contourArea(contour)

            # Ignore small noisy contours
            if area < 1000:
                continue

            # Approximate contour
            epsilon = 0.02 * cv2.arcLength(contour, True)

            approx = cv2.approxPolyDP(contour, epsilon, True)

            # BOX DETECTION
            # Box will approximately have 4 corners
            if len(approx) == 4:

                target_found = True

                # Get bounding rectangle
                x, y, w, h = cv2.boundingRect(approx)

                # Calculate centroid
                cx = int(x + w / 2)
                cy = int(y + h / 2)

                # Draw visualization
                cv2.drawContours(frame, [approx], -1, (0, 255, 0), 3)

                cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)

                cv2.putText(
                    frame,
                    "BOX TARGET",
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )

                # Publish target info
                target_msg = Point()

                target_msg.x = float(cx)
                target_msg.y = float(cy)
                target_msg.z = float(area)

                self.target_publisher.publish(target_msg)

                self.get_logger().info(
                    f"Target Detected -> X: {cx}, Area: {area:.2f}"
                )

                break

        if not target_found:

            target_msg = Point()

            target_msg.x = -1.0
            target_msg.y = -1.0
            target_msg.z = -1.0

            self.target_publisher.publish(target_msg)

        # Display output
        cv2.imshow("Perception Output", frame)

        cv2.waitKey(1)


def main(args=None):

    rclpy.init(args=args)

    node = PerceptionNode()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()

    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()