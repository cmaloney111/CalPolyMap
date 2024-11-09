from dash import dcc, html
import dash_daq as daq
import dash_bootstrap_components as dbc

def create_layout():
    return html.Div([
        # For getting width
        dcc.Location(id='url'),  
        html.Div(id='viewport-container', style={'display': 'none'}),

        # Title
        html.H1("Smart Route Finder", style={'text-align': 'center', 'color': '#333', 'margin-bottom': '20px'}),
        
        dbc.Alert(
            children="Please provide a start location and end location.",
            id='alert-message',
            dismissable=True,  # Makes it dismissible by clicking 'X'
            is_open=False,  # Initially hidden
            color='danger',  # Makes the alert red
            style={'position': 'fixed', 'top': '50%', 'left': '50%', 'transform': 'translate(-50%, -50%)', 
                   'width': '80%', 'text-align': 'center', 'z-index': '1000'}
        ),
        # Main input section (start node, end node, POIs)
        html.Div([
            create_input_section(),
            create_poi_section(),
        ], style={'display': 'flex', 'align-items': 'center', 'justify-content': 'center', 'padding': '15px',
                  'background-color': '#f9f9f9', 'border-radius': '5px', 'box-shadow': '0 2px 4px rgba(0, 0, 0, 0.1)',
                  'flex-wrap': 'wrap', 'gap': '10px'}),

        # Dynamic waypoint inputs
        html.Div(id='waypoint-inputs', children=[], style={'margin-top': '10px'}),
        
        # Buttons for waypoints
        html.Div([
            html.Button('Add Waypoint', id='add-waypoint-button', n_clicks=0, style={'margin-bottom': '20px', 'margin-right': '5px',
                'background-color': '#007bff', 'color': 'white', 'padding': '10px 15px', 'border': 'none', 'margin-top': '10px',
                'border-radius': '5px', 'cursor': 'pointer', 'font-size': '14px', 'transition': 'background-color 0.3s ease'
            }),
            html.Button('Remove All Waypoints', id='remove-all-waypoints-button', n_clicks=0, style={'margin-bottom': '20px', 'margin-right': '5px',
                'background-color': '#dc3545', 'color': 'white', 'padding': '10px 15px', 'border': 'none', 'margin-top': '10px',
                'border-radius': '5px', 'cursor': 'pointer', 'font-size': '14px', 'transition': 'background-color 0.3s ease', 'margin-right': '10px'
            }),
            html.Label("Walking Speed:", style={'margin-left': '10px'}),
            dcc.Input(
                id='walking-speed-input',
                type='number',
                min=0.01,
                placeholder='Enter speed (m/s)',
                style={
                    'margin-left': '10px',
                    'margin-bottom': '10px', 
                    'padding': '5px', 
                    'width': '200px', 
                    'border': '1px solid #ccc', 
                    'border-radius': '5px',
                    'box-shadow': '0 2px 4px rgba(0, 0, 0, 0.1)',
                    'transition': 'border-color 0.3s ease'
                }
            )
        ], style={'margin-bottom': '20px'}),
        
        # Container for find path button, heuristics, and time display
        create_find_path_container(),
        
        # Graph to display the path
        dcc.Graph(id='path-plot', style={'height': '100vw', 'width': '80%', 'margin': '0 auto'}),
        
    ], style={'position': 'relative', 'padding': '20px', 'background-color': '#ffffff',
              'border-radius': '10px', 'box-shadow': '0 4px 8px rgba(0, 0, 0, 0.1)'})

def create_input_section():
    # Create dropdown inputs for start and end locations
    return html.Div([
        html.Div([html.Label("Start Location:", style={'margin-bottom': '5px', 'display': 'inline-block'}), dcc.Dropdown(id='start-node-dropdown', options=[], multi=False,
                                                              placeholder="Select Start Location", 
                                                              style={'width': '100%', 'border-radius': '5px', 'outline': 'thick', 'box-sizing': 'border-box'})], 
                                                              style={'width': '100%', 'margin-bottom': '20px', 'box-sizing': 'border-box'}),
        html.Div([html.Label("End Location:", style={'margin-bottom': '5px', 'display': 'inline-block'}), dcc.Dropdown(id='end-node-dropdown', options=[], multi=False,
                                                            placeholder="Select End Location",
                                                            style={'width': '100%', 'border-radius': '5px', 'outline': 'thick', 'box-sizing': 'border-box'})],
                                                            style={'width': '100%', 'box-sizing': 'border-box'}),
    ], className='input-wrapper', style={'display': 'flex', 'flex-direction': 'column','align-items': 'flex-start','padding': '10px', 'box-sizing': 'border-box'})
    
def create_poi_section():
    # Create POI section with color picker and input fields
    return html.Div(
        id='add-poi-modal',
        children=[
            html.H3("Add Point of Interest (POI)", style={'margin-bottom': '10px', 'color': '#333'}),
            html.Div([
                html.Label("Name:", style={'margin-right': '10px'}), dcc.Input(id='poi-name', type='text', placeholder="Name", style={
                        'width': '120px', 'margin-right': '10px', 'padding': '10px', 'border-radius': '5px', 'border': '1px solid #ccc'
                    }),
                html.Label("Lat:", style={'margin-right': '10px'}), dcc.Input(id='poi-lat', type='number', placeholder="Latitude", style={
                        'width': '120px', 'margin-right': '10px', 'padding': '10px', 'border-radius': '5px', 'border': '1px solid #ccc'
                    }),
                html.Label("Lon:", style={'margin-right': '10px'}), dcc.Input(id='poi-lon', type='number', placeholder="Longitude", style={
                        'width': '120px', 'margin-right': '10px', 'padding': '10px', 'border-radius': '5px', 'border': '1px solid #ccc'
                    }),
            ], id='poi-inputs', style={'display': 'flex', 'justify-content': 'center', 'align-items': 'center', 'margin-bottom': '10px'}),
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
            daq.ColorPicker(id='poi-color', value=dict(hex='#119DFF'), size=180, style={
                'display': 'none', 'margin-right': '193px', 'margin-top': '95px', 'position': 'absolute', 'z-index': '10000'
            })
        ], style={'display': 'flex', 'flex-direction': 'column', 'align-items': 'center', 'border': '1px solid #ccc', 'margin-top': '20px',
                  'padding': '15px', 'border-radius': '5px', 'margin-left': 'auto'}
    )

def create_find_path_container():
    # Container for find path button and time display
    return html.Div(
        children=[
            html.Button('Find Path', id='submit-button', n_clicks=0, style={'margin-right': '20px',
                'background-color': '#17a2b8', 'color': 'white', 'padding': '10px 15px', 'border': 'none',
                'border-radius': '5px', 'cursor': 'pointer', 'font-size': '14px', 'transition': 'background-color 0.3s ease'
            }),
            dcc.Dropdown(id='heuristic-dropdown', options=[
                {'label': 'None', 'value': 'None'},
                {'label': 'Geodesic', 'value': 'Geodesic'},
                {'label': 'No waypoints', 'value': 'No waypoints'}
            ], multi=False, placeholder="Select Heuristic", style={
                 'width': '162px', 'border-radius': '5px', 'margin-bottom': '20px', 'margin-top': '20px', 'margin-right': '20px', 'border-radius': '5px'}),
            html.Label("Total time:"),
            dcc.Input(
                id='time-input',
                type='number',
                min=0,
                placeholder='Enter time (minutes)',
                style={
                    'margin-left': '10px',
                    'margin-right': '10px',
                    'padding': '5px', 
                    'width': '200px', 
                    'border': '1px solid #ccc', 
                    'border-radius': '5px',
                    'box-shadow': '0 2px 4px rgba(0, 0, 0, 0.1)',
                    'transition': 'border-color 0.3s ease'
                }
            ),
            html.Div(id='time-display', style={
                'padding': '10px', 'font-size': '18px', 'font-weight': 'bold', 'color': '#28a745', 'padding': '5px 10px', 'border-radius': '0px',
                'background-color': 'white', 'align-self': 'center',
            })
        ], style={'display': 'flex', 'align-items': 'center', 'margin-bottom': '20px'}
    )