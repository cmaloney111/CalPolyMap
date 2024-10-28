import plotly.graph_objects as go
from util.mapUtil import locationFromTag, addPOI, getTagName
import util.generalUtil
import util.algorithmsUtil
from dash import dcc, html, Input, Output, State, callback_context
from dash.dependencies import ALL
import math
import time
from util.buildingUtil import expression_set
from util.mapUtil import extractPath, getPathDetails
from visualization import plotMap, smooth_path

global cityMap
base_map = None
y_level = 1.0
poi_set = set()
options_list = sorted(expression_set)

def generate_options(value):
    # Generate options list for dropdown based on value
    final_options = []
    filtered_options = [option for option in options_list if value.lower() in option.lower()] if value else options_list
    for i, opt in enumerate(filtered_options):
        final_options.append({'label': opt, 'value': opt})
        final_options.append({'label': '——————————————————', 'value': opt + str(i) + opt, 'disabled': True})
    return final_options

def register_callbacks(app, currCityMap):
    global cityMap
    cityMap = currCityMap
    
    # Client-side callback to get viewport dimensions
    app.clientside_callback(
        """
        function(href) {
            var w = window.innerWidth;
            return w
        }
        """,
        Output('viewport-container', 'children'),
        Input('url', 'href')
    )

    @app.callback(
        Output('start-node-dropdown', 'options'),
        Input('start-node-dropdown', 'search_value')
    )
    def update_start_node_options(value):
        return generate_options(value)

    @app.callback(
        Output('end-node-dropdown', 'options'),
        Input('end-node-dropdown', 'search_value')
    )
    def update_end_node_options(value):
        return generate_options(value)

    @app.callback(
        Output({'type': 'waypoint', 'index': ALL}, 'options'),
        Input({'type': 'waypoint', 'index': ALL}, 'search_value')
    )
    def update_waypoint_options(values):
        return [generate_options(value) for value in values]

    @app.callback(
        Output('path-plot', 'style'),
        Output('poi-color', 'style'),
        Input('color-button', 'n_clicks'),
        Input('viewport-container', 'children'),
        State('poi-color', 'style')
    )
    def toggle_color_picker(n_clicks, width, current_style):
        if width is None:
            return {'height': '500px', 'width': '90%', 'margin': '0 auto'}, current_style
        height = ((42.5 - 0.0075 * width) * width) / (1 + math.log(1 + (50 * width), 9)) / 10
        if n_clicks > 0:
            if width < 611:
                margin_top = '65px'
            elif width < 981:
                margin_top = '-40px'
            else:
                margin_top = '105px'
            
            # Toggle visibility
            if current_style.get('display') == 'none':
                return {'width': '90%', 'height': f'{height}px', 'margin': '0 auto'}, {
                    'margin-right': '193px',
                    'margin-top': margin_top,
                    'display': 'inline-block',
                    'position': 'absolute',
                    'z-index': '10000'
                }
            else:
                return {'height': f'{height}px', 'width': '90%', 'margin': '0 auto'}, {'display': 'none'}
            
        return {'height': f'{height}px', 'width': '90%', 'margin': '0 auto'}, current_style


    @app.callback(
    Output('waypoint-inputs', 'children'),
    [Input('add-waypoint-button', 'n_clicks'),
     Input({'type': 'remove-waypoint-button', 'index': ALL}, 'n_clicks'),
     Input('remove-all-waypoints-button', 'n_clicks')],
    [State('waypoint-inputs', 'children')]
    )
    def manage_waypoints(add_clicks, remove_clicks, remove_all_clicks, waypoint_inputs):
        # Track the button clicks for adding and removing waypoints
        ctx = callback_context
        if not ctx.triggered:
            return waypoint_inputs

        # Determine which input triggered the callback
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

        # Add a new waypoint
        if triggered_id == 'add-waypoint-button':
            new_index = len(waypoint_inputs)
            new_input = html.Div([
                            html.Div(
                                dcc.Dropdown(
                                    id={'type': 'waypoint', 'index': new_index},
                                    options=[],
                                    className='waypoint-dropdown',
                                    multi=False,
                                    placeholder=f'Waypoint {new_index + 1}',
                                    style={
                                        'border-radius': '5px', 
                                        'border': '1px solid #ccc', 
                                        'width': '100%', 
                                        'box-shadow': '0 2px 4px rgba(0, 0, 0, 0.1)',
                                        'transition': 'border-color 0.3s ease',
                                        'display': 'block',
                                    }
                                ),
                                style={
                                    'width': '100%',
                                    'box-sizing': 'border-box',
                                    'border-radius': '5px',
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
                            'width': '350px',
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
                input_component = child['props']['children'][0]['props']['children']
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
        Input('time-display', 'style'),
        Input('time-display', 'children'),
        Input('add-poi-button', 'n_clicks'),
        Input('poi-color', 'value')],
        State('start-node-dropdown', 'value'),
        State({'type': 'waypoint', 'index': ALL}, 'value'),
        State('end-node-dropdown', 'value'),
        State('poi-name', 'value'), 
        State('poi-lat', 'value'), 
        State('poi-lon', 'value'),
        State('heuristic-dropdown', 'value')
    )
    def update_output(path_n_clicks, current_style, current_val, poi_n_clicks, poi_color,
                    start_node, waypoints, end_node, poi_name, lat, lon, heuristic):
        ctx = callback_context

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
                    global poi_set
                    poi_set.add(poi_name)
                    print(poi_name)
                    options_list.append(poi_name)
                    addPOI(cityMap, poi_name, lat, lon)
                    return base_map, current_val, current_style

        if path_n_clicks > 0:
            start_node = getTagName(start_node)
            end_node = getTagName(end_node)
            if len(waypoints) == 0:
                problem = util.algorithmsUtil.ShortestPathProblem(start_node, end_node, cityMap)
                if heuristic == 'Geodeic':
                    problem = util.algorithmsUtil.aStarReduction(problem, util.algorithmsUtil.Geodesic(problem, cityMap))
                elif heuristic == 'No waypoints':
                    problem = util.algorithmsUtil.aStarReduction(problem, util.algorithmsUtil.NoWaypoints(end_node, cityMap))
                ucs = util.generalUtil.UniformCostSearch(verbose=0)
                start_time = time.time()
                ucs.solve(problem)
                end_time = time.time()
                
                path = extractPath(problem.startState().location, ucs)
                parsedPath, parsedWaypoints = getPathDetails(path=path, waypointTags=[], cityMap=cityMap)
            else:
                waypoints = [waypoint for waypoint in waypoints if waypoint != None]
                print(waypoints)
                waypoints = list(map(getTagName, waypoints))
                ucs = util.generalUtil.UniformCostSearch(verbose=1)
                problem = util.algorithmsUtil.WaypointsShortestPathProblem(
                    start_node,
                    waypoints,
                    end_node,
                    cityMap,
                )
                if heuristic == 'Geodesic':
                    problem = util.algorithmsUtil.aStarReduction(problem, util.algorithmsUtil.Geodesic(problem, cityMap))
                elif heuristic == 'No waypoints':
                    problem = util.algorithmsUtil.aStarReduction(problem, util.algorithmsUtil.NoWaypoints(end_node, cityMap))
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
                        marker=dict(size=10, color="Black"),
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
                direction="down",
                showactive=True,
                x=0.5, 
                xanchor="center",
                y=y_level,
                yanchor="top",
            )


            base_map.update_layout(
                updatemenus=list(base_map['layout']['updatemenus']) + [path_button]
            )

            return base_map, time_display, {**current_style, 'background-color': '#f0f0f0', 'box-shadow': '0 1px 3px rgba(0, 0, 0, 0.1)'}
        else:
            base_map = plotMap(
                        cityMap=cityMap,
                        mapName="",
                        mapbox_token="pk.eyJ1IjoiY21hbG9uZXkxMTEiLCJhIjoiY20xeDRhejcyMHJ5MDJtcWJmbXh2MmV5eSJ9.1JLW7GG-tuhjlKCJZt8PZg",
                    ) 
            return base_map, "", current_style
