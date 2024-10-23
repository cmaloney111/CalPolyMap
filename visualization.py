import argparse
from typing import List, Tuple
import plotly.graph_objects as go
from mapUtil import CityMap, addLandmarks, readMap, loadMap, locationFromTag, getTotalCost, addPOI
import util
import copy
import algorithms
from collections import defaultdict
import numpy as np
from dash import Dash, dcc, html, Input, Output, State
from dash.dependencies import ALL
import dash
import dash_daq as daq
import time

args = None
cityMap = None
base_map = None
y_level = 1.156
all_paths_trace_idx = None
path_trace_indices = []

def interpolate_points(lat1, lon1, lat2, lon2, num_points=10) -> Tuple[List[float]]:
    """
    Interpolate between two geographical points.

    :param lat1: Latitude of the first point.
    :param lon1: Longitude of the first point.
    :param lat2: Latitude of the second point.
    :param lon2: Longitude of the second point.
    :param num_points: Number of points to generate between the two points.
    :return: Two lists containing the interpolated latitudes and longitudes.
    """
    latitudes = np.linspace(lat1, lat2, num=num_points)
    longitudes = np.linspace(lon1, lon2, num=num_points)
    return latitudes.tolist(), longitudes.tolist()


def smooth_path(
    solutionLat: List[float], solutionLon: List[float], num_points=10
) -> Tuple[List[float]]:
    """
    Smooth the path by interpolating between points.

    :param solutionLat: List of latitudes in the path.
    :param solutionLon: List of longitudes in the path.
    :param num_points: Number of points to generate between each pair of points.
    :return: Two lists of smooth latitudes and longitudes.
    """
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

def plotMap(
    cityMap: CityMap,
    mapName: str,
    mapbox_token: str,
):
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

    fig = go.Figure()

    # ---- Add the trace for all walkable paths (Connections) ----
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
    all_paths_trace_idx = len(fig.data) - 1  # Store the trace index for All Walkable Paths

    
    # ---- Add traces for landmarks, amenities, and buildings ----
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

    colors = {"Landmarks": "purple", "Amenities": "blue", "Buildings": "orange"}
    trace_indices = defaultdict(list)

    # Adding traces for the categories
    for category in ["Landmarks", "Amenities", "Buildings"]:
        for item_type, locations in organized_map[category].items():
            for lat, lon, loc_id in locations:
                trace_name = f"{category}/{item_type}"
                trace = go.Scattermapbox(
                    lat=[lat],
                    lon=[lon],
                    text=loc_id,
                    name=trace_name,
                    mode="markers",
                    marker=dict(size=8, color=colors[category]),
                    visible=True
                )
                fig.add_trace(trace)
                trace_indices[category].append(len(fig.data) - 1)

    # ---- Add updatemenus for the buttons ----
    global y_level

    all_paths_button = dict(
        active=-1,
        type="buttons",
        buttons=[
            dict(
                label="Show all Walkable Paths",
                method="restyle",
                args=[{"visible": True}, [all_paths_trace_idx]],
                args2=[{"visible": "legendonly"}, [all_paths_trace_idx]],
            ),
        ],
        direction="left",
        showactive=True,
        x=0.575,  # Adjust position for each toggle
        xanchor="left",
        y=y_level,
        yanchor="top",
    )
    landmarks_config = dict(
        type="buttons",
        buttons=[
            dict(
                label="Landmarks",
                method="restyle",
                args=[{"visible": True}, trace_indices["Landmarks"]],
                args2=[{"visible": "legendonly"}, trace_indices["Landmarks"]],
            )
        ],
        direction="left",
        showactive=True,
        x=0.24,  # Position on the map
        xanchor="left",
        y=y_level,
        yanchor="top",
    )

    amenities_config = dict(
        type="buttons",
        buttons=[
            dict(
                label="Amenities",
                method="restyle",
                args=[{"visible": True}, trace_indices["Amenities"]],
                args2=[{"visible": "legendonly"}, trace_indices["Amenities"]],
            ),
        ],
        direction="left",
        showactive=True,
        x=0.36,  # Adjust position for each toggle
        xanchor="left",
        y=y_level,
        yanchor="top",
    )

    buildings_config = dict(
        type="buttons",
        buttons=[
            dict(
                label="Buildings",
                method="restyle",
                args=[{"visible": True}, trace_indices["Buildings"]],
                args2=[{"visible": "legendonly"}, trace_indices["Buildings"]],
            ),
        ],
        direction="left",
        showactive=True,
        x=0.47,  # Adjust position for each toggle
        xanchor="left",
        y=y_level,
        yanchor="top",
    )

    # Add your original map style dropdown buttons
    dropdown_map_styles = dict(
        buttons=[
            {
                "label": "Outdoors",
                "method": "relayout",
                "args": [{"mapbox.style": "outdoors"}],
            },
            {
                "label": "Streets",
                "method": "relayout",
                "args": [{"mapbox.style": "streets"}],
            },
            {
                "label": "Satellite",
                "method": "relayout",
                "args": [{"mapbox.style": "satellite"}],
            },
            {
                "label": "Satellite Streets",
                "method": "relayout",
                "args": [{"mapbox.style": "satellite-streets"}],
            },
            {"label": "Dark", "method": "relayout", "args": [{"mapbox.style": "dark"}]},
            {
                "label": "Light",
                "method": "relayout",
                "args": [{"mapbox.style": "light"}],
            },
            {
                "label": "Basic",
                "method": "relayout",
                "args": [{"mapbox.style": "basic"}],
            },
        ],
        direction="down",
        showactive=True,
        x=0.797,
        xanchor="left",
        y=y_level,
        yanchor="top",
    )

    # Add dropdowns for category toggles
    fig.update_layout(
        updatemenus=[
            all_paths_button,
            landmarks_config,
            amenities_config,
            buildings_config,
            dropdown_map_styles
        ],
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
        legend={
            "title": {"text": "Legend"},  # Custom title for the legend
            "traceorder": "reversed",     # Show most recent traces on top
            "uirevision": True            # Enable search functionality
        },
    )

    return fig

# Initialize Dash app
app = Dash(__name__)

# Define the layout of the app
app.layout = html.Div([
    html.H1("Shortest Path Finder", style={'text-align': 'center', 'color': '#333', 'margin-bottom': '20px'}),

    # Start, End, and Add POI row
    html.Div([
        # Start node input
        html.Div([
            html.Label("Start Location:", style={'margin-right': '5px', 'margin-bottom': '0'}),
            dcc.Input(id='start-node', type='text', value='', style={
                'margin-right': '20px', 'padding': '10px', 'border-radius': '5px', 'border': '1px solid #ccc', 'width': '180px'
            }),
        ], style={'margin-right': '20px'}),  # Wrapper div for spacing

        # End node input
        html.Div([
            html.Label("End Location:", style={'margin-right': '5px', 'margin-bottom': '0'}),
            dcc.Input(id='end-node', type='text', value='', style={
                'margin-right': '50px', 'padding': '10px', 'border-radius': '5px', 'border': '1px solid #ccc', 'width': '180px'
            }),
        ], style={'margin-right': '20px'}),  # Wrapper div for spacing

        # Add POI section
        html.Div(
            id='add-poi-modal',
            children=[
                html.H3("Add Point of Interest (POI)", style={'margin-bottom': '10px', 'color': '#333'}),
                html.Div([
                    html.Label("Name:", style={'margin-right': '10px'}),
                    dcc.Input(id='poi-name', type='text', placeholder="Name", style={
                        'width': '120px', 'margin-right': '10px', 'padding': '10px', 'border-radius': '5px', 'border': '1px solid #ccc'
                    }),

                    html.Label("Lat:", style={'margin-right': '10px'}),
                    dcc.Input(id='poi-lat', type='number', placeholder="Latitude", style={
                        'width': '80px', 'margin-right': '10px', 'padding': '10px', 'border-radius': '5px', 'border': '1px solid #ccc'
                    }),

                    html.Label("Lon:", style={'margin-right': '10px'}),
                    dcc.Input(id='poi-lon', type='number', placeholder="Longitude", style={
                        'width': '80px', 'padding': '10px', 'border-radius': '5px', 'border': '1px solid #ccc'
                    }),
                ], style={'display': 'flex', 'justify-content': 'center', 'align-items': 'center', 'margin-bottom': '10px'}),  # Updated style

                # Add POI button
                html.Button('Add POI', id='add-poi-button', n_clicks=0, style={
                    'background-color': '#28a745', 'color': 'white', 'padding': '10px 15px',
                    'border': 'none', 'border-radius': '5px', 'cursor': 'pointer', 'font-size': '14px',
                    'transition': 'background-color 0.3s ease', 'margin-right': '10px', 'margin-bottom': '10px'
                }),
                html.Button('Choose a color', id='color-button', n_clicks=0, style={
                    'background-color': '#28a745', 'color': 'white', 'padding': '10px 15px',
                    'border': 'none', 'border-radius': '5px', 'cursor': 'pointer', 'font-size': '14px',
                    'transition': 'background-color 0.3s ease', 'margin-right': '10px', 'margin-bottom': '10px'
                }),
                daq.ColorPicker(
                    id='poi-color',
                    value=dict(hex='#119DFF'),
                    size=180,
                    style={'display': 'None'}), 
            ],
            style={'display': 'flex', 'flex-direction': 'column', 'align-items': 'center', 'border': '1px solid #ccc', 'padding': '15px', 'border-radius': '5px'}
        )
    ], style={'display': 'flex', 'align-items': 'center', 'margin-bottom': '20px', 'padding': '15px', 'background-color': '#f9f9f9', 'border-radius': '5px', 'box-shadow': '0 2px 4px rgba(0, 0, 0, 0.1)'}),

    # Waypoints section with dynamic inputs
    html.Div(id='waypoint-inputs', children=[]),

    # Button to add more waypoints
    html.Button('Add Waypoint', id='add-waypoint-button', n_clicks=0, style={'margin-bottom': '20px', 'margin-right': '5px',
        'background-color': '#007bff', 'color': 'white', 'padding': '10px 15px', 'border': 'none',
        'border-radius': '5px', 'cursor': 'pointer', 'font-size': '14px', 'transition': 'background-color 0.3s ease'
    }),

    # Button to remove a waypoint
    html.Button('Remove All Waypoints', id='remove-all-waypoints-button', n_clicks=0, style={'margin-bottom': '20px', 'margin-right': '5px',
        'background-color': '#dc3545', 'color': 'white', 'padding': '10px 15px', 'border': 'none',
        'border-radius': '5px', 'cursor': 'pointer', 'font-size': '14px', 'transition': 'background-color 0.3s ease'
    }),

    # Container for the Find Path button and Time to find path text
    html.Div(style={'display': 'flex', 'align-items': 'center', 'margin-bottom': '20px'}, children=[

        # Button to find the path
        html.Button('Find Path', id='submit-button', n_clicks=0, style={'margin-right': '20px',
            'background-color': '#17a2b8', 'color': 'white', 'padding': '10px 15px', 'border': 'none',
            'border-radius': '5px', 'cursor': 'pointer', 'font-size': '14px', 'transition': 'background-color 0.3s ease'
        }),

        # Time display
        html.Div(id='time-display', style={
            'font-size': '18px',
            'font-weight': 'bold',
            'color': '#28a745',
            'padding': '5px 10px',
            'border-radius': '0px',
            'background-color': 'white',
            'align-self': 'center',  # Center align vertically
        }),
    ]),

    # Legend search bar
    html.Div(
        dcc.Input(
            id="legend-search", 
            type="text", 
            placeholder="Search legend...", 
            style={
                'width': '170px',
                'padding': '10px', 
                'border-radius': '5px', 
                'border': '1px solid #ccc', 
                'position': 'absolute',  
                'top': '30px',  
                'right': '30px',  
                'z-index': '1000', 
                'background-color': 'white'
            }
        ),
        style={'position': 'relative'}
    ),

    # Graph to display the path
    dcc.Graph(id='path-plot'),

], style={'position': 'relative', 'padding': '20px', 'background-color': '#ffffff', 'border-radius': '10px', 'box-shadow': '0 4px 8px rgba(0, 0, 0, 0.1)'})

# Callback to toggle the color picker visibility
@app.callback(
    Output('poi-color', 'style'),
    Input('color-button', 'n_clicks'),
    State('poi-color', 'style')
)
def toggle_color_picker(n_clicks, current_style):
    if n_clicks > 0:
        # If clicked, toggle visibility by changing the display property
        if current_style.get('display').lower() == 'none':
            return {'margin-right': '193px', 'margin-top': '95px', 'display': 'inline-block', 'position': 'absolute', 'z-index': '10000'}
        else:
            return {'display': 'none'}
    return current_style

@app.callback(
    Output('waypoint-inputs', 'children'),
    [Input('add-waypoint-button', 'n_clicks'),
     Input({'type': 'remove-waypoint-button', 'index': ALL}, 'n_clicks'),
     Input('remove-all-waypoints-button', 'n_clicks')],
    [State('waypoint-inputs', 'children')]
)
def manage_waypoints(add_clicks, remove_clicks, remove_all_clicks, waypoint_inputs):
    # Track the button clicks for adding and removing waypoints
    ctx = dash.callback_context
    if not ctx.triggered:
        return waypoint_inputs

    # Determine which input triggered the callback
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Add a new waypoint
    if triggered_id == 'add-waypoint-button':
        new_index = len(waypoint_inputs)
        new_input = html.Div([
                        dcc.Input(
                            id={'type': 'waypoint', 'index': new_index},
                            type='text',
                            placeholder=f'Waypoint {new_index + 1}',
                            style={
                                'padding': '10px', 
                                'border-radius': '5px', 
                                'border': '1px solid #ccc', 
                                'width': '200px', 
                                'box-shadow': '0 2px 4px rgba(0, 0, 0, 0.1)',
                                'transition': 'border-color 0.3s ease',
                            }
                        ),
                        html.Button(
                            'Remove', 
                            id={'type': 'remove-waypoint-button', 'index': new_index}, 
                            style={
                                'margin-left': '10px', 
                                'background-color': '#dc3545', 
                                'color': 'white', 
                                'padding': '10px 15px', 
                                'border': 'none', 
                                'border-radius': '5px', 
                                'cursor': 'pointer', 
                                'font-size': '14px',
                                'transition': 'background-color 0.3s ease, transform 0.2s ease',
                                'box-shadow': '0 2px 4px rgba(0, 0, 0, 0.1)',
                            }
                        )
                    ], style={
                        'display': 'flex',
                        'align-items': 'center',
                        'justify-content': 'space-between',
                        'margin-bottom': '10px',
                        'padding': '10px',
                        'border-radius': '5px',
                        'border': '1px solid #e0e0e0',
                        'background-color': '#f9f9f9',
                        'box-shadow': '0 2px 4px rgba(0, 0, 0, 0.1)',
                        'transition': 'background-color 0.3s ease',
                        'width': '30%',
                    })
        waypoint_inputs.append(new_input)

    # Remove all waypoints
    elif triggered_id == 'remove-all-waypoints-button':
        waypoint_inputs = []

    # Remove an individual waypoint
    elif 'remove-waypoint-button' in triggered_id:
        # Extract the index of the waypoint to remove
        idx_to_remove = int(triggered_id.split('"index":')[1].split("}")[0].split(',')[0])
        waypoint_inputs = [child for child in waypoint_inputs if f'\'index\': {idx_to_remove}' not in str(child)]
        for i, child in enumerate(waypoint_inputs):
            # Extract and update the placeholder and id of the input
            input_component = child['props']['children'][0]
            remove_button = child['props']['children'][1]

            # Update the placeholder and ids to reflect the new position
            input_component['props']['id'] = {'type': 'waypoint', 'index': i}
            input_component['props']['placeholder'] = f'Waypoint {i+1}'
            remove_button['props']['id'] = {'type': 'remove-waypoint-button', 'index': i}


    return waypoint_inputs

@app.callback(
    [Output('path-plot', 'figure'),
     Output('time-display', 'children'),
     Output('time-display', 'style')],
    [Input('submit-button', 'n_clicks'),
     Input('legend-search', 'value'),
     Input('time-display', 'style'),
     Input('time-display', 'children'),
     Input('add-poi-button', 'n_clicks'),
     Input('poi-color', 'value')],
    State('start-node', 'value'),
    State({'type': 'waypoint', 'index': ALL}, 'value'),
    State('end-node', 'value'),
    State('poi-name', 'value'), 
    State('poi-lat', 'value'), 
    State('poi-lon', 'value')
)
def update_output(n_clicks, search_value, current_style, current_val, poi_n_clicks, poi_color,
                  start_node, waypoints, end_node, poi_name, lat, lon):
    ctx = dash.callback_context

    if ctx.triggered:
        global base_map, cityMap
        # Determine which input triggered the callback
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]


        if triggered_id == 'add-poi-button':
            if poi_n_clicks > 0 and poi_name and lat and lon:
                base_map.add_trace(
                    go.Scattermapbox(
                        lat=[lat],
                        lon=[lon],
                        mode="markers",
                        marker=dict(size=10, color=poi_color['hex']),   
                        name=poi_name,
                        visible=True
                    )
                )
                addPOI(cityMap, poi_name, lat, lon)
                return base_map, current_val, current_style
            
        if triggered_id == 'legend-search':
            global all_paths_trace_idx, path_trace_indices
            filtered_fig = copy.deepcopy(base_map)

            # Filter traces based on search term
            if filtered_fig:
                for i, trace in enumerate(filtered_fig.data):
                    if i == all_paths_trace_idx or not trace.visible or i in path_trace_indices:
                        continue
                    if search_value and search_value.lower() not in trace.name.lower():
                        trace.visible = False
                    else:
                        trace.visible = True 

            return filtered_fig, current_val, current_style
        
    global args

    if n_clicks > 0:
        if len(waypoints) == 0:
            problem = algorithms.ShortestPathProblem(start_node, end_node, cityMap)
            ucs = util.UniformCostSearch(verbose=0)
            start_time = time.time()
            ucs.solve(problem)
            end_time = time.time()
            
            path = extractPath(problem.startLocation, ucs)
            parsedPath, parsedWaypoints = getPathDetails(path=path, waypointTags=[], cityMap=cityMap)
        else:
            ucs = util.UniformCostSearch(verbose=0)
            problem = algorithms.WaypointsShortestPathProblem(
                start_node,
                waypoints,
                end_node,
                cityMap,
            )
            start_time = time.time()
            ucs.solve(problem)
            end_time = time.time()
            path = extractPath(locationFromTag(start_node, cityMap), ucs)
            parsedPath, parsedWaypoints = getPathDetails(path=path, waypointTags=waypoints, cityMap=cityMap)

        elapsed_time = end_time - start_time

        time_display = f"Time to find path: {elapsed_time:.6f} seconds"

        
        solutionLat, solutionLon = [], []
        path_connections = [(parsedPath[i], parsedPath[i + 1]) for i in range(len(parsedPath) - 1)]
        for source, target in path_connections:
            solutionLat.append(cityMap.geoLocations[source].latitude)
            solutionLat.append(cityMap.geoLocations[target].latitude)
            solutionLat.append(None)
            solutionLon.append(cityMap.geoLocations[source].longitude)
            solutionLon.append(cityMap.geoLocations[target].longitude)
            solutionLon.append(None)

        # Smooth path
        smooth_lat, smooth_lon = smooth_path(solutionLat, solutionLon)

        start_lat, start_lon = smooth_lat[0], smooth_lon[0]  # First point
        end_lat, end_lon = smooth_lat[-1], smooth_lon[-1]    # Last point

        # Remove the existing path trace
        traces = list(base_map.data)
        remove_list = ['Path', 'Start', 'End', 'Waypoint']
        base_map.data = [trace for trace in traces if trace.name not in remove_list]



        # Add the smooth path trace
        base_map.add_trace(
            go.Scattermapbox(
                lat=smooth_lat,
                lon=smooth_lon,
                mode="lines",
                line=dict(width=6, color="red"),
                name="Path",
                visible=True
            )
        )

        # Add the start point as a large green dot
        base_map.add_trace(
            go.Scattermapbox(
                lat=[start_lat],
                lon=[start_lon],
                mode="markers",
                marker=dict(size=14, color="Green"),   
                name="Start",
                visible=True
            )
        )

        # Add the end point as a large purple dot
        base_map.add_trace(
            go.Scattermapbox(
                lat=[end_lat],
                lon=[end_lon],
                mode="markers",
                marker=dict(size=14, color="Purple"),
                name="End",
                visible=True
            )
        )

        path_trace_indices = [len(base_map.data) - 3, len(base_map.data) - 2, len(base_map.data) - 1]

        for waypoint in parsedWaypoints:
            lat = cityMap.geoLocations[waypoint].latitude
            lon = cityMap.geoLocations[waypoint].longitude
            base_map.add_trace(
                go.Scattermapbox(
                    lat=[lat],
                    lon=[lon],
                    mode="markers",
                    marker=dict(size=10, color="White"),
                    name="Waypoint",
                    visible=True
                )
            )
            path_trace_indices.append(len(base_map.data) - 1)

        if base_map['layout']['updatemenus'][-1]['buttons'][0]['label'] == "Show Path":
            base_map['layout']['updatemenus'] = base_map['layout']['updatemenus'][:-1]
        global y_level
        path_button = dict(
            type="buttons",
            buttons=[
                dict(
                    label="Show Path",
                    method="restyle",
                    args=[{"visible": True}, path_trace_indices],
                    args2=[{"visible": "legendonly"}, path_trace_indices],
                ),
            ],
            direction="left",
            showactive=True,
            x=0.794, 
            xanchor="left",
            y=y_level,
            yanchor="top",
        )

        base_map['layout']['updatemenus'][-1]['x'] = 0.907
    
        base_map.update_layout(
            updatemenus=list(base_map['layout']['updatemenus']) + [path_button]
        )

        return base_map, time_display, {**current_style, 'background-color': '#f0f0f0', 'box-shadow': '0 1px 3px rgba(0, 0, 0, 0.1)'}
    else:
        base_map = plotMap(
                    cityMap=cityMap,
                    mapName="Cal Poly Map",
                    mapbox_token=args.mapbox_token,
                ) 
        return base_map, "", current_style

def extractPath(startLocation: str, search: util.SearchAlgorithm) -> List[str]:
    """
    Assumes that `solve()` has already been called on the `searchAlgorithm`.

    We extract a sequence of locations from `search.path`.
    """
    return [startLocation] + search.actions

def getPathDetails(
    path: List[str],
    waypointTags: List[str],
    cityMap: CityMap,
) -> Tuple[List[str], List[str]]:
    """Print the path details and return the parsed path and waypoint tags."""
    doneWaypoints = set()
    doneWaypointTags = set()
    for location in path:
        for tag in cityMap.tags[location]:
            if tag in waypointTags:
                doneWaypoints.add(location)
                doneWaypointTags.add(tag)
        tagsStr = " ".join(cityMap.tags[location])
        doneTagsStr = " ".join(sorted(doneWaypointTags))
        print(f"Location {location} tags:[{tagsStr}]; done:[{doneTagsStr}]")

    total_distance = getTotalCost(path, cityMap)
    print(f"Total distance: {total_distance}")

    # Return the path and tags as a tuple
    return path, list(doneWaypoints)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--large-pbf", action="store_true", help="Use large pbf file (slower)"
    )
    parser.add_argument(
        "--landmark-file",
        type=str,
        default="data/calpoly-landmarks.json",
        help="Landmarks (.json)",
    )
    parser.add_argument(
        "--mapbox-token",
        type=str,
        default="pk.eyJ1IjoiY21hbG9uZXkxMTEiLCJhIjoiY20xeDRhejcyMHJ5MDJtcWJmbXh2MmV5eSJ9.1JLW7GG-tuhjlKCJZt8PZg",
        help="Mapbox access token for visualization",
    )
    args = parser.parse_args()
    if args.large_pbf:
        args.map_file = "./data/sanluisobispo.pbf"
    else:
        args.map_file = "./data/calpoly.pbf"

    # Create cityMap and populate any relevant landmarks
    # cityMap = readMap("./data/calpoly.pbf")
    cityMap = loadMap(args.large_pbf)
    addLandmarks(cityMap, args.landmark_file)
    
    app.run_server(debug=True)
