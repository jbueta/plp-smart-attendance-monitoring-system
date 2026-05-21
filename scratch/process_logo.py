import cv2
import numpy as np
import os

def process_logo(input_path, output_path):
    print(f"Reading image from {input_path}")
    # Read the image
    img = cv2.imread(input_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        print("Error: Could not read image.")
        return False
    
    # Ensure it's in BGRA format
    if img.shape[2] == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
    
    h, w = img.shape[:2]
    print(f"Image dimensions: {w}x{h}")
    
    # Convert to grayscale for contour detection
    gray = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
    
    # Threshold the image to isolate the white background
    # Since background is white (255), we threshold to find non-white region
    _, thresh = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY_INV)
    
    # Find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        print("Error: No contours found.")
        return False
        
    # Get the largest contour, which should be the circular logo
    largest_contour = max(contours, key=cv2.contourArea)
    
    # Fit a minimum enclosing circle to the largest contour
    (x, y), radius = cv2.minEnclosingCircle(largest_contour)
    center = (int(x), int(y))
    radius = int(radius)
    
    print(f"Detected circle: center={center}, radius={radius}")
    
    # Create an empty alpha mask (all transparent)
    mask = np.zeros((h, w), dtype=np.uint8)
    
    # Draw a filled white circle on the mask
    # We reduce the radius slightly (e.g. by 1 pixel) to get a perfect clean edge
    cv2.circle(mask, center, radius - 1, 255, -1)
    
    # Set the alpha channel of the image to match the mask
    img[:, :, 3] = mask
    
    # Optional: Crop the image to the circle bounds to make it a perfect square
    # Let's crop it with a small margin of 2 pixels around the circle
    margin = 2
    x_start = max(0, center[0] - radius - margin)
    x_end = min(w, center[0] + radius + margin)
    y_start = max(0, center[1] - radius - margin)
    y_end = min(h, center[1] + radius + margin)
    
    cropped = img[y_start:y_end, x_start:x_end]
    
    # Save the processed image
    cv2.imwrite(output_path, cropped)
    print(f"Saved processed logo to {output_path}")
    return True

if __name__ == "__main__":
    input_file = r"C:\Users\PLPASIG\.gemini\antigravity\brain\086cc606-71ef-4854-9aad-385f2a2bd168\media__1779385129967.png"
    output_file = r"c:\Users\PLPASIG\.gemini\antigravity\scratch\plp_monitoring_system\static\images\PLP1999_Logo.png"
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    success = process_logo(input_file, output_file)
    if success:
        print("Background removal completed successfully!")
    else:
        print("Failed to remove background.")
