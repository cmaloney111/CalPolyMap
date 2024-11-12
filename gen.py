from open3d import *
cloud = io.read_point_cloud("output.ply") 
visualization.draw_geometries([cloud]) 
            