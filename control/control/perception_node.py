#!/usr/bin/env python3
"""
Fixed Vision Node for Box Detection
- Works with SOLID BLACK shapes on GRAY background
- Detects box by shape analysis
- Displays frame with GREEN boundary around detected box
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
        
        # Subscribe to camera
        self.image_subscriber = self.create_subscription(
            Image,
            '/camera/image_raw',
            self.image_callback,
            10
        )
        
        # Publish target position
        self.target_publisher = self.create_publisher(Point, '/target_info', 10)
        
        self.get_logger().info("Fixed Vision Node Started")


    def image_callback(self, msg):
        """Process camera image and detect box"""
        
        try:
            # Convert ROS image to OpenCV
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            frame = cv2.resize(frame, (640, 480))
            
            # Output frame with segmentation
            output_frame = frame.copy()
            
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # For SOLID BLACK shapes on GRAY background
            # Use threshold to get binary image
            # Black shapes = low intensity (0-50), gray background = high intensity (150+)
            _, binary = cv2.threshold(gray, 80, 255, cv2.THRESH_BINARY_INV)
            
            # Clean up the binary image
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
            
            # Find contours
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            self.get_logger().info(f"Found {len(contours)} contours")
            
            target_found = False
            
            # Analyze each contour
            for i, contour in enumerate(contours):
                area = cv2.contourArea(contour)
                
                # Filter by area (ignore small noise)
                if area < 1000:
                    continue
                
                # Approximate contour to polygon
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                # Get bounding rectangle
                x, y, w, h = cv2.boundingRect(approx)
                
                # Calculate aspect ratio
                aspect_ratio = float(w) / h if h > 0 else 0
                
                self.get_logger().info(
                    f"Contour {i}: vertices={len(approx)}, area={area:.0f}, "
                    f"aspect_ratio={aspect_ratio:.2f}, w/h={w}/{h}"
                )
                
                # KEY DETECTION: Check if it's a box (4 corners + roughly square)
                if len(approx) == 4:

                    pts = approx.reshape(4, 2)

                    side_lengths = []

                    for j in range(4):

                        p1 = pts[j]
                        p2 = pts[(j + 1) % 4]

                        distance = np.linalg.norm(p1 - p2)

                        side_lengths.append(distance)

                    avg_side = np.mean(side_lengths)

                    side_tolerance = 0.20 * avg_side

                    square_condition = all(
                        abs(side - avg_side) < side_tolerance
                        for side in side_lengths
                    )

                    if not square_condition:
                        continue

                    if 0.6 <= aspect_ratio <= 1.4:
                        
                        # Calculate centroid
                        M = cv2.moments(contour)
                        if M['m00'] > 0:
                            cx = int(M['m10'] / M['m00'])
                            cy = int(M['m01'] / M['m00'])
                            
                            # GREEN rectangle boundary
                            cv2.rectangle(output_frame, (x, y), (x + w, y + h), (0, 255, 0), 3)
                            
                            # GREEN contour outline
                            cv2.drawContours(output_frame, [approx], 0, (0, 255, 0), 2)
                            
                            # RED dot at center
                            cv2.circle(output_frame, (cx, cy), 8, (0, 0, 255), -1)
                            
                            # Label
                            cv2.putText(output_frame, 'BOX', (x, y - 15),
                                      cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
                            
                            # Publish
                            target_msg = Point()
                            target_msg.x = float(cx)
                            target_msg.y = float(cy)
                            target_msg.z = float(area)
                            self.target_publisher.publish(target_msg)
                            
                            target_found = True
                            self.get_logger().info(f"✓ BOX DETECTED at ({cx}, {cy}), Area: {area:.0f}")
                            break
            
            if not target_found:
                # No box found
                target_msg = Point()
                target_msg.x = -1.0
                target_msg.y = -1.0
                target_msg.z = -1.0
                self.target_publisher.publish(target_msg)
                
                # Add search message on frame
                cv2.putText(output_frame, 'Searching for Box...', (20, 40),
                          cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 2)
            
            # Show info on frame
            cv2.putText(output_frame, f'Contours found: {len(contours)}', (20, output_frame.shape[0] - 20),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            
            # Display segmented frame with boundaries
            cv2.imshow("Box Detection", output_frame)
            cv2.waitKey(1)
            
        except Exception as e:
            self.get_logger().error(f"Error in image processing: {str(e)}")


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