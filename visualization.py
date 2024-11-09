from typing import List, Tuple
import plotly.graph_objects as go
from collections import defaultdict
import numpy as np


y_level = 1.0
all_paths_trace_idx = None

def interpolate_points(lat1, lon1, lat2, lon2, num_points=10) -> Tuple[List[float]]:
    latitudes = np.linspace(lat1, lat2, num=num_points)
    longitudes = np.linspace(lon1, lon2, num=num_points)
    return latitudes.tolist(), longitudes.tolist()


def smooth_path(
    solutionLat: List[float], solutionLon: List[float], num_points=10
) -> Tuple[List[float]]:
    smooth_lat = []
    smooth_lon = []
    solutionLat = [lat for lat in solutionLat if lat is not None]
    solutionLon = [lon for lon in solutionLon if lon is not None]

    for i in range(len(solutionLat) - 1):
        lat_segment, lon_segment = interpolate_points(
            solutionLat[i],
            solutionLon[i],
            solutionLat[i + 1],
            solutionLon[i + 1],
            num_points,
        )
        smooth_lat.extend(lat_segment)
        smooth_lon.extend(lon_segment)

    return smooth_lat, smooth_lon

def extract_connections(cityMap):
    latitude, longitude = [], []
    connections = [
        (source, target)
        for source in cityMap.distances
        for target in cityMap.distances[source]
    ]
    for source, target in connections:
        latitude.append(cityMap.geoLocations[source].latitude)
        latitude.append(cityMap.geoLocations[target].latitude)
        latitude.append(None)
        longitude.append(cityMap.geoLocations[source].longitude)
        longitude.append(cityMap.geoLocations[target].longitude)
        longitude.append(None)
    return latitude, longitude

def organize_locations(cityMap):
    organized_map = defaultdict(lambda: defaultdict(list))
    for location_id, latLon in cityMap.geoLocations.items():
        tags = cityMap.tags[location_id]
        for tag in tags:
            if "landmark=" in tag:
                category = "Landmarks"
                landmark_type = tag.split("landmark=")[1]
                organized_map[category][landmark_type].append(
                    (latLon.latitude, latLon.longitude, location_id)
                )
            elif "amenity=" in tag:
                category = "Amenities"
                amenity_type = tag.split("amenity=")[1]
                organized_map[category][amenity_type].append(
                    (latLon.latitude, latLon.longitude, location_id)
                )
            elif "building=" in tag:
                category = "Buildings"
                building_type = tag.split("building=")[1]
                organized_map[category][building_type].append(
                    (latLon.latitude, latLon.longitude, location_id)
                )
    return organized_map

def add_traces(fig, latitude, longitude, organized_map):
    colors = {"Landmarks": "purple", "Amenities": "blue", "Buildings": "orange"}
    trace_indices = defaultdict(list)

    # Add trace for all walkable paths
    fig.add_trace(
        go.Scattermapbox(
            lat=latitude,
            lon=longitude,
            mode="lines",
            line=dict(width=1.5, color="blue"),
            name="All Walkable Paths",
            visible=False  # Initially hidden
        )
    )
    global all_paths_trace_idx
    all_paths_trace_idx = len(fig.data) - 1

    # Add traces for categories
    for category, types in organized_map.items():
        for item_type, locations in types.items():
            for lat, lon, loc_id in locations:
                trace = go.Scattermapbox(
                    lat=[lat],
                    lon=[lon],
                    text=loc_id,
                    name=f"{item_type}",
                    mode="markers",
                    marker=dict(size=8, color=colors[category]),
                    visible=True
                )
                fig.add_trace(trace)
                trace_indices[category].append(len(fig.data) - 1)
    return trace_indices

def configure_dropdowns(trace_indices):
    button_dropdown = dict(
        buttons=[
            dict(
                label="Walkable Paths",
                method="restyle",
                args=[{"visible": True}, [all_paths_trace_idx]],
                args2=[{"visible": "legendonly"}, [all_paths_trace_idx]],
            ),
            dict(
                label="Landmarks",
                method="restyle",
                args=[{"visible": True}, trace_indices["Landmarks"]],
                args2=[{"visible": "legendonly"}, trace_indices["Landmarks"]],
            ),
            dict(
                label="Amenities",
                method="restyle",
                args=[{"visible": True}, trace_indices["Amenities"]],
                args2=[{"visible": "legendonly"}, trace_indices["Amenities"]],
            ),
            dict(
                label="Buildings",
                method="restyle",
                args=[{"visible": True}, trace_indices["Buildings"]],
                args2=[{"visible": "legendonly"}, trace_indices["Buildings"]],
            ),
        ],
        direction="down",
        showactive=True,
        x=0.01,
        xanchor="left",
        y=1.0,
        yanchor="top",
    )
    
    dropdown_map_styles = dict(
        buttons=[
            {"label": "Outdoors", "method": "relayout", "args": [{"mapbox.style": "outdoors"}]},
            {"label": "Streets", "method": "relayout", "args": [{"mapbox.style": "streets"}]},
            {"label": "Satellite", "method": "relayout", "args": [{"mapbox.style": "satellite"}]},
            {"label": "Satellite Streets", "method": "relayout", "args": [{"mapbox.style": "satellite-streets"}]},
            {"label": "Dark", "method": "relayout", "args": [{"mapbox.style": "dark"}]},
            {"label": "Light", "method": "relayout", "args": [{"mapbox.style": "light"}]},
            {"label": "Basic", "method": "relayout", "args": [{"mapbox.style": "basic"}]},
        ],
        direction="down",
        showactive=True,
        x=0.99,
        xanchor="right",
        y=1.0,
        yanchor="top",
    )
    
    return [button_dropdown, dropdown_map_styles]

def configure_layout(fig, mapbox_token, mapName, latitude, longitude, dropdowns):
    fig.update_layout(
        updatemenus=dropdowns,
        mapbox=dict(
            accesstoken=mapbox_token,
            style="outdoors",
            center=dict(
                lat=latitude[len(latitude) // 2],
                lon=longitude[len(longitude) // 2],
            ),
            zoom=15,
        ),
        title=mapName,
        margin={"r": 0, "t": 73, "l": 0, "b": 0},
        showlegend=False,
    )

def plotMap(cityMap, mapName, mapbox_token):
    fig = go.Figure()

    latitude, longitude = extract_connections(cityMap)
    organized_map = organize_locations(cityMap)

    trace_indices = add_traces(fig, latitude, longitude, organized_map)
    dropdowns = configure_dropdowns(trace_indices)

    configure_layout(fig, mapbox_token, mapName, latitude, longitude, dropdowns)
    return fig
