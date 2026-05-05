#!/usr/bin/env python3

"""
Optimized Vision Node for Cube Detection
- Detects cube-like target object
- Rejects cylinders and circular objects
- Handles perspective distortion and tilted views
- Uses geometric contour analysis
"""

import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Image
from geometry_msgs.msg import Point

from cv_bridge import CvBridge

import cv2
import numpy as np


class SimpleVisionNode(Node):

    def __init__(self):

        super().__init__('vision_node')

        self.bridge = CvBridge()

        self.image_subscriber = self.create_subscription(
            Image,
            '/camera/image_raw',
            self.image_callback,
            10
        )

        self.target_publisher = self.create_publisher(
            Point,
            '/target_info',
            10
        )

        self.get_logger().info("Optimized Cube Detection Vision Node Started")


    def angle_between(self, p1, p2, p3):

        a = np.array(p1) - np.array(p2)
        b = np.array(p3) - np.array(p2)

        cosine_angle = np.dot(a, b) / (
            np.linalg.norm(a) * np.linalg.norm(b)
        )

        angle = np.degrees(
            np.arccos(
                np.clip(cosine_angle, -1.0, 1.0)
            )
        )

        return angle


    def image_callback(self, msg):

        try:

            frame = self.bridge.imgmsg_to_cv2(
                msg,
                desired_encoding='bgr8'
            )

            frame = cv2.resize(frame, (640, 480))

            output_frame = frame.copy()

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            _, binary = cv2.threshold(
                gray,
                80,
                255,
                cv2.THRESH_BINARY_INV
            )

            kernel = cv2.getStructuringElement(
                cv2.MORPH_ELLIPSE,
                (5, 5)
            )

            binary = cv2.morphologyEx(
                binary,
                cv2.MORPH_CLOSE,
                kernel
            )

            binary = cv2.morphologyEx(
                binary,
                cv2.MORPH_OPEN,
                kernel
            )

            contours, _ = cv2.findContours(
                binary,
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE
            )

            cv2.putText(
                output_frame,
                f'Contours: {len(contours)}',
                (20, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2
            )

            target_found = False

            for i, contour in enumerate(contours):

                area = cv2.contourArea(contour)

                if area < 1000:
                    continue

                perimeter = cv2.arcLength(contour, True)

                epsilon = 0.02 * perimeter

                approx = cv2.approxPolyDP(
                    contour,
                    epsilon,
                    True
                )

                self.get_logger().info(
                    f'Contour {i}: '
                    f'Vertices={len(approx)}, '
                    f'Area={area:.1f}'
                )

                if len(approx) != 4:
                    continue

                if not cv2.isContourConvex(approx):

                    self.get_logger().info(
                        "Rejected: Non-convex"
                    )

                    continue

                circularity = (
                    4 * np.pi * area /
                    (perimeter * perimeter)
                )

                self.get_logger().info(
                    f'Circularity={circularity:.3f}'
                )

                if circularity > 0.88:

                    self.get_logger().info(
                        "Rejected: Circular Object"
                    )

                    continue

                pts = approx.reshape(4, 2)

                side_lengths = []

                for j in range(4):

                    p1 = pts[j]
                    p2 = pts[(j + 1) % 4]

                    side = np.linalg.norm(p1 - p2)

                    side_lengths.append(side)

                avg_side = np.mean(side_lengths)

                side_tolerance = 0.25 * avg_side

                equal_sides = all(
                    abs(side - avg_side) < side_tolerance
                    for side in side_lengths
                )

                if not equal_sides:

                    self.get_logger().info(
                        "Rejected: Unequal Sides"
                    )

                    continue

                angles = []

                for j in range(4):

                    p1 = pts[j - 1]
                    p2 = pts[j]
                    p3 = pts[(j + 1) % 4]

                    angle = self.angle_between(
                        p1,
                        p2,
                        p3
                    )

                    angles.append(angle)

                valid_angles = all(
                    60 <= angle <= 120
                    for angle in angles
                )

                if not valid_angles:

                    self.get_logger().info(
                        "Rejected: Invalid Angles"
                    )

                    continue

                rect = cv2.minAreaRect(contour)

                box_points = cv2.boxPoints(rect)

                box_points = np.int32(box_points)

                M = cv2.moments(contour)

                if M['m00'] <= 0:
                    continue

                cx = int(M['m10'] / M['m00'])
                cy = int(M['m01'] / M['m00'])

                cv2.drawContours(
                    output_frame,
                    [box_points],
                    0,
                    (0, 255, 0),
                    3
                )

                cv2.circle(
                    output_frame,
                    (cx, cy),
                    8,
                    (0, 0, 255),
                    -1
                )

                cv2.putText(
                    output_frame,
                    'TARGET BOX',
                    (cx - 80, cy - 20),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.9,
                    (0, 255, 0),
                    2
                )

                cv2.putText(
                    output_frame,
                    f'Area: {int(area)}',
                    (cx - 80, cy + 20),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 255),
                    2
                )

                target_msg = Point()

                target_msg.x = float(cx)
                target_msg.y = float(cy)
                target_msg.z = float(area)

                self.target_publisher.publish(target_msg)

                target_found = True

                self.get_logger().info(
                    f'✓ TARGET BOX DETECTED '
                    f'at ({cx}, {cy}) '
                    f'Area={area:.1f}'
                )

                break

            if not target_found:

                target_msg = Point()

                target_msg.x = -1.0
                target_msg.y = -1.0
                target_msg.z = -1.0

                self.target_publisher.publish(target_msg)

                cv2.putText(
                    output_frame,
                    'Searching for Target Box...',
                    (20, 70),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.0,
                    (0, 0, 255),
                    2
                )

            cv2.imshow(
                "Optimized Cube Detection",
                output_frame
            )

            cv2.waitKey(1)

        except Exception as e:

            self.get_logger().error(
                f'Error in image processing: {str(e)}'
            )


def main(args=None):

    rclpy.init(args=args)

    node = SimpleVisionNode()

    try:

        rclpy.spin(node)

    except KeyboardInterrupt:

        pass

    finally:

        node.destroy_node()

        rclpy.shutdown()

        cv2.destroyAllWindows()


if __name__ == '__main__':

    main()