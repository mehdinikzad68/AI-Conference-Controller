"""
Camera Test Script for AI-Symp-Controller

Tests camera connectivity and functionality using OpenCV.
This script verifies that the camera can be accessed and displays live video frames.

Run this script before proceeding with Face AI module implementation.

Usage:
    python camera_test.py [camera_index]
    
    camera_index: Optional camera device index (default: 0)
                  Use index 1, 2, etc. for additional cameras

Exit Methods (Cross-Platform, Any Keyboard Language):
    - Press 'q' key (requires window to have keyboard focus)
    - Click the window close (X) button - works regardless of keyboard language
      or focus. This method uses OpenCV's native window property check for
      reliable exit on all systems and keyboard layouts.
"""

import cv2
import sys


def test_camera(camera_index: int = 0):
    """
    Test camera access and display live video feed.
    
    This function monitors the window visibility property on every loop iteration
    to ensure clean exit when the window is closed via the X button, regardless
    of keyboard language or focus state. This provides cross-platform compatibility
    and reliable cleanup.
    
    Args:
        camera_index: Camera device index (0 for default, 1+ for additional cameras)
    
    Exit Conditions:
        - Window closed (X button): Detected via cv2.getWindowProperty() check
        - 'q' key pressed: Standard keyboard exit (requires window focus)
        - Camera frame read failure: After 5 consecutive failures
    """
    print(f"Attempting to initialize camera at index {camera_index}...")
    
    # Attempt to initialize the camera
    cap = cv2.VideoCapture(camera_index)
    
    if not cap.isOpened():
        print("\n" + "="*60)
        print("ERROR: Camera not found or not accessible.")
        print("="*60)
        print("\nPossible causes:")
        print("1. Camera is not connected or powered on")
        print("2. Camera is being used by another application")
        print("3. Camera drivers are not installed or outdated")
        print("4. Camera is disabled in privacy settings (Windows)")
        print("5. Wrong camera index - try index 1, 2, or higher")
        print("\nTroubleshooting steps:")
        print("- Check if camera works in other applications (Camera app, Zoom, etc.)")
        print("- Try a different camera index: python camera_test.py 1")
        print("- Check Windows Privacy settings: Settings > Privacy > Camera")
        print("- Restart the application and try again")
        print("- If using external camera, ensure it's properly connected")
        print("="*60)
        sys.exit(1)
    
    print(f"✓ Camera initialized successfully at index {camera_index}")
    print("\nCamera test window opened.")
    print("Exit methods:")
    print("  - Press 'q' key (requires window focus)")
    print("  - Click the window close (X) button (works from any keyboard language)")
    print("-"*60)
    
    # Get camera properties for information
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    print(f"Camera Resolution: {width}x{height}")
    if fps > 0:
        print(f"Camera FPS: {fps:.2f}")
    
    frame_count = 0
    error_count = 0
    window_name = 'Camera Test - Press Q to Quit'
    
    while True:
        ret, frame = cap.read()
        
        if not ret:
            error_count += 1
            print(f"Warning: No frame detected (attempt {error_count})")
            
            # Exit after 5 consecutive failures
            if error_count >= 5:
                print("\n" + "="*60)
                print("ERROR: Failed to capture frames from camera.")
                print("="*60)
                print("\nPossible causes:")
                print("1. Camera disconnected during operation")
                print("2. Camera hardware failure")
                print("3. Insufficient permissions")
                print("4. Camera driver issues")
                print("\nPlease check camera connection and try again.")
                print("="*60)
                break
        
        else:
            # Reset error count on successful frame
            error_count = 0
            frame_count += 1
            
            # Display frame count on the video (optional, top-left corner)
            cv2.putText(frame, f"Frames: {frame_count}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # Display the frame
            cv2.imshow(window_name, frame)
        
        # Check if window is closed by user (X button clicked) - cross-platform
        # This check works regardless of keyboard language or window focus
        try:
            # WND_PROP_VISIBLE returns a value < 1 when window is closed
            if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                print("\n✓ Window closed (X button). Exiting gracefully.")
                print(f"Total frames captured: {frame_count}")
                break
        except cv2.error:
            # Window might have been destroyed, exit gracefully
            # This handles cases where window was destroyed externally
            print("\n✓ Window closed. Exiting gracefully.")
            print(f"Total frames captured: {frame_count}")
            break
        
        # Quit on 'q' press - works only if window has keyboard focus
        # Note: This requires English keyboard or proper focus, unlike X button method
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            print("\n✓ 'q' pressed. Exiting gracefully.")
            print(f"Total frames captured: {frame_count}")
            break
        elif key == ord('c'):
            # Additional feature: press 'c' to try next camera
            print(f"\nTrying next camera index ({camera_index + 1})...")
            cap.release()
            cv2.destroyAllWindows()
            test_camera(camera_index + 1)
            return
    
    # Clean up - ensures camera is released and windows are closed
    # This cleanup executes regardless of exit method (X button or 'q' key)
    cap.release()
    cv2.destroyAllWindows()
    
    print("\n" + "="*60)
    print("CAMERA TEST SUCCESSFUL")
    print("="*60)
    print("Your camera is working correctly and ready for AI development.")
    print("Camera released and window closed.")
    print("You can now proceed with Face AI module implementation.")
    print("="*60)


def main():
    """Main entry point."""
    print("="*60)
    print("AI-Symp-Controller - Camera Test Script")
    print("="*60)
    print("\nThis script tests camera connectivity and functionality.")
    print("Required for Face AI module development.")
    print()
    
    # Check if camera index provided as command-line argument
    camera_index = 0
    if len(sys.argv) > 1:
        try:
            camera_index = int(sys.argv[1])
            print(f"Using camera index: {camera_index}")
        except ValueError:
            print(f"Invalid camera index '{sys.argv[1]}', using default (0)")
    
    try:
        test_camera(camera_index)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print("\n" + "="*60)
        print("UNEXPECTED ERROR")
        print("="*60)
        print(f"Error: {str(e)}")
        print("\nPlease report this error for troubleshooting.")
        print("="*60)
        sys.exit(1)


if __name__ == "__main__":
    main()

