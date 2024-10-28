import argparse
from util.mapUtil import addLandmarks, loadMap
import dash_bootstrap_components as dbc
import dash
from layout import create_layout
from callbacks import register_callbacks

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = create_layout()
    
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
    args = parser.parse_args()

    if args.large_pbf:
        args.map_file = "./data/sanluisobispo.pbf"
    else:
        args.map_file = "./data/calpoly.pbf"

    # cityMap = readMap(args.map_file)
    cityMap = loadMap(args.large_pbf)
    addLandmarks(cityMap, args.landmark_file)

    register_callbacks(app, cityMap)
    app.run_server(debug=True)