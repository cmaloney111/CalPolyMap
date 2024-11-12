import open3d as o3d
import numpy as np
import json
import time

zoom_counter = 0
zoom_factor = 0.3  # Adjust this to control the zoom speed

def custom_zoom(vis, zoom_factor):
    global zoom_counter
    # Get the current view status
    view_stat = json.loads(vis.get_view_status())['trajectory'][0]

    # Get the current lookat point and camera location
    lookat = np.array(view_stat['lookat'])
    front = np.array(view_stat['front'])

    # Move the camera closer to the lookat point based on zoom factor
    view_ctl = vis.get_view_control()
    new_lookat = lookat - front * zoom_factor
    view_ctl.set_lookat(new_lookat)

    # Print zoom factor for verification
    print(f"Current Zoom Factor: {zoom_factor}")
    print(f"Current Zoom Counter: {zoom_counter}")
    
    # Optionally, read new camera parameters after certain zoom steps
    if zoom_counter == 48:
        parameters = o3d.io.read_pinhole_camera_parameters("data/sc_2.json")
        view_ctl.convert_from_pinhole_camera_parameters(parameters, True)
    
    zoom_counter += 1

def auto_trigger_zoom(vis, zoom_factor, max_zoom=180):
    """
    Automatically triggers the zoom function repeatedly until max_zoom is reached.
    """
    global zoom_counter
    if zoom_counter < max_zoom:
        custom_zoom(vis, zoom_factor)  # Trigger the zoom
        time.sleep(0.1)  # Add a small delay to simulate animation timing
        # Continue zooming until max_zoom is reached
        vis.register_animation_callback(lambda vis: auto_trigger_zoom(vis, zoom_factor, max_zoom))

def key_callback(vis):
    global zoom_counter
    zoom_counter = 0  # Reset zoom counter when Z is pressed

    view_ctl = vis.get_view_control()
    parameters = o3d.io.read_pinhole_camera_parameters("data/sc.json")
    view_ctl.convert_from_pinhole_camera_parameters(parameters, True)

    print("Z key pressed, starting zoom.")
    auto_trigger_zoom(vis, zoom_factor)  # Trigger the zoom process

def main():
    # Load the point cloud
    cloud = o3d.io.read_point_cloud("output.ply")

    # Create the Open3D visualizer
    visualizer = o3d.visualization.VisualizerWithKeyCallback()
    visualizer.create_window()
    visualizer.add_geometry(cloud)
    view_ctl = visualizer.get_view_control()
    parameters = o3d.io.read_pinhole_camera_parameters("data/sc.json")
    view_ctl.convert_from_pinhole_camera_parameters(parameters, True)

    # Register the key callback for 'Z' key
    visualizer.register_key_callback(ord("Z"), key_callback)

    # Run the visualizer
    visualizer.run()
    visualizer.destroy_window()

if __name__ == "__main__":
    main()
