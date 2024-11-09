import json
from collections import defaultdict
from dataclasses import dataclass
from math import asin, cos, radians, sin, sqrt
from typing import Dict, List, Optional, Set, Tuple
import osmium
import requests
from requests.structures import CaseInsensitiveDict
from osmium import osm
from util.buildingUtil import buildings_set, amenities_set
from util.generalUtil import SearchAlgorithm

RADIUS_EARTH = 6371000  # meters
UNIT_DELTA = 0.00001 # more or less true for SLO (see https://en.wikipedia.org/wiki/Decimal_degrees)

@dataclass(frozen=True)
class GeoLocation:
    latitude: float
    longitude: float

    def __repr__(self):
        return f"{self.latitude},{self.longitude}"

class CityMap:
    def __init__(self) -> None:
        self.geoLocations: Dict[str, GeoLocation] = {} # names to lat-lon
        self.tags: Dict[str, List[str]] = defaultdict(list) # tags corresponding to labels
        self.distances: Dict[str, Dict[str, float]] = defaultdict(dict) # distance between two labels

    def addLocation(self, label: str, location: GeoLocation, tags: List[str]) -> None:
        assert label not in self.geoLocations, f"Location {label} already added"
        self.geoLocations[label] = location
        self.tags[label] = [makeTag("label", label)] + tags

    def addConnection(self, source: str, target: str, distance: Optional[float] = None) -> None:
        if distance is None:
            distance = computeDistance(self.geoLocations[source], self.geoLocations[target])
        self.distances[source][target] = distance
        self.distances[target][source] = distance

    def saveCityMap(self, filename: str) -> None:
        data = {
            "geoLocations": {
                label: (loc.latitude, loc.longitude)
                for label, loc in self.geoLocations.items()
            },
            "tags": self.tags,
            "distances": self.distances,
        }
        with open(filename, "w") as f:
            json.dump(data, f, indent=4)

    def loadCityMap(self, filename: str) -> None:
        with open(filename, "r") as f:
            data = json.load(f)
        self.geoLocations = {
            label: GeoLocation(lat, lon)
            for label, (lat, lon) in data["geoLocations"].items()
        }
        self.tags = defaultdict(list, data["tags"])
        self.distances = defaultdict(dict, data["distances"])


def extractPath(startLocation: str, search: SearchAlgorithm) -> List[str]:
    return [startLocation] + search.actions

def getPathDetails(
    path: List[str],
    waypointTags: List[str],
    cityMap: CityMap,
) -> Tuple[List[str], List[str]]:
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
    return path, list(doneWaypoints), total_distance

def addLandmarks(cityMap: CityMap, landmarkPath: str, toleranceMeters: float = 250.0) -> None:
    with open(landmarkPath) as f:
        landmarks = json.load(f)

    for item in landmarks:
        latitudeString, longitudeString = item["geo"].split(",")
        geo = GeoLocation(float(latitudeString), float(longitudeString))
        bestDistance, bestLabel = min(
            (computeDistance(geo, existingGeo), existingLabel)
            for existingLabel, existingGeo in cityMap.geoLocations.items()
        )
        if bestDistance < toleranceMeters:
            for key in ["landmark", "amenity"]:
                if key in item:
                    cityMap.tags[bestLabel].append(makeTag(key, item[key]))


def addPOI(
    cityMap: CityMap, name: str, lat: float, lon: float, toleranceMeters: float = 250.0
) -> None:
    geo = GeoLocation(lat, lon)
    bestDistance, bestLabel = min(
        (computeDistance(geo, existingGeo), existingLabel)
        for existingLabel, existingGeo in cityMap.geoLocations.items()
    )
    if bestDistance < toleranceMeters:
        cityMap.tags[bestLabel].append(makeTag("POI", name))


def makeTag(key: str, value: str) -> str:
    return f"{key}={value}"


def locationFromTag(tag: str, cityMap: CityMap) -> Optional[str]:
    possibleLocations = sorted([location for location, tags in cityMap.tags.items() if tag in tags])
    if len(possibleLocations) > 0:
        return possibleLocations[0]
    return None

def getTagName(tag_orig: str) -> str:
    from callbacks import poi_set
    if tag_orig in buildings_set:
        return 'building=' + tag_orig
    elif tag_orig in amenities_set:
        return 'amenity=' + tag_orig
    elif tag_orig in poi_set:
        return 'POI=' + tag_orig
    else:
        return 'landmark=' + tag_orig


def computeDistance(geo1: GeoLocation, geo2: GeoLocation) -> float:
    """
    Haversine distance between two coordinates (https://en.wikipedia.org/wiki/Haversine_formula)
    """
    lon1, lat1 = radians(geo1.longitude), radians(geo1.latitude)
    lon2, lat2 = radians(geo2.longitude), radians(geo2.latitude)

    deltaLon, deltaLat = lon2 - lon1, lat2 - lat1
    haversine = (sin(deltaLat / 2) ** 2) + (cos(lat1) * cos(lat2)) * (
        sin(deltaLon / 2) ** 2
    )
    return 2 * RADIUS_EARTH * asin(sqrt(haversine))

def getTotalCost(path: List[str], cityMap: CityMap) -> float:
    cost = 0.0
    for i in range(len(path) - 1):
        cost += cityMap.distances[path[i]][path[i + 1]]
    return cost


def fetch_buildings_here(bounding_box: list) -> list:
    url = f"https://api.geoapify.com/v2/places?categories=building&filter=rect:{bounding_box[0]},{bounding_box[1]},{bounding_box[2]},{bounding_box[3]}&limit=500&apiKey=013f1a5e29924d5594fd2555481dcd1d"

    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json"
    response = requests.get(url, headers=headers)
    data = response.json()
    buildings = []
    for item in data.get("features", []):
        name = item["properties"].get(
            "name", "Unnamed Building"
        )
        lon = item["geometry"]["coordinates"][0] 
        lat = item["geometry"]["coordinates"][1]
        buildings.append({"name": name, "lon": lon, "lat": lat})
    return buildings


def divide_bounding_box(bounding_box: list, rows: int, cols: int) -> List[list]:
    min_lon, min_lat, max_lon, max_lat = bounding_box
    lat_step = (max_lat - min_lat) / rows
    lon_step = (max_lon - min_lon) / cols

    subregions = []
    for i in range(rows):
        for j in range(cols):
            sub_min_lon = min_lon + j * lon_step
            sub_max_lon = min_lon + (j + 1) * lon_step
            sub_min_lat = min_lat + i * lat_step
            sub_max_lat = min_lat + (i + 1) * lat_step
            subregions.append([sub_min_lon, sub_min_lat, sub_max_lon, sub_max_lat])

    return subregions


def readMap(osmPath: str, getBuildings: bool = False, saveMap: bool = False) -> CityMap:
    class MapCreationHandler(osmium.SimpleHandler):
        def __init__(self) -> None:
            super().__init__()
            self.nodes: Dict[str, GeoLocation] = {}
            self.tags: Dict[str, List[str]] = defaultdict(list)
            self.edges: Set[Tuple[str, str]] = set()
            self.unconnected_nodes: Set[str] = set() 
            self.connected_nodes: Set[str] = set()

        def node(self, n: osm.Node) -> None:
            tags = [makeTag(tag.k, tag.v) for tag in n.tags]
            self.tags[str(n.id)] = tags
            if len(tags) > 0:
                self.nodes[str(n.id)] = GeoLocation(n.location.lat, n.location.lon)
                self.unconnected_nodes.add(str(n.id)) 

        def way(self, w: osm.Way) -> None:
            pathType = w.tags.get("highway", None)
            if pathType is None or pathType in {
                "motorway",
                "motorway_link",
                "trunk",
                "trunk_link",
            }:
                return
            elif w.tags.get("pedestrian", "n/a") == "no" or w.tags.get("foot", "n/a") == "no":
                return

            wayNodes = w.nodes
            for sourceIdx in range(len(wayNodes) - 1):
                s, t = wayNodes[sourceIdx], wayNodes[sourceIdx + 1]
                sLabel, tLabel = str(s.ref), str(t.ref)
                sLoc = GeoLocation(s.location.lat, s.location.lon)
                tLoc = GeoLocation(t.location.lat, t.location.lon)

                assert sLoc != tLoc, "Source and Target are the same location!"

                self.nodes[sLabel], self.nodes[tLabel] = sLoc, tLoc
                self.connected_nodes.update([sLabel, tLabel]) 
                self.unconnected_nodes.discard(sLabel)
                self.unconnected_nodes.discard(tLabel)

                self.edges.add((sLabel, tLabel))

        def connect_unconnected_nodes(self):
            for node in self.unconnected_nodes:
                node_loc = self.nodes[node]
                closest_node, closest_distance = min(
                    (
                        (connected_node, computeDistance(node_loc, self.nodes[connected_node]))
                        for connected_node in self.connected_nodes
                    ),
                    key=lambda pair: pair[1]
                )

                self.edges.add((node, closest_node))
                self.connected_nodes.add(node) 

    mapCreator = MapCreationHandler()
    mapCreator.apply_file(osmPath, locations=True)

    if getBuildings:
        bounding_box = [-120.678, 35.294, -120.651, 35.310]
        subregions = divide_bounding_box(bounding_box, 2, 2)
        all_buildings = []

        for subregion in subregions:
            buildings = fetch_buildings_here(subregion)
            all_buildings.extend(buildings)

        with open('data/building_locations.json', 'w') as f:
            json.dump(all_buildings, f, indent=2)


    with open("data/building_locations.json", "r") as f:
        buildings = json.load(f)

    already_used_location_ids = {}
    for building in buildings:
        location_id = building["name"].replace(" ", "_")
        if location_id in already_used_location_ids:
            continue
        already_used_location_ids[location_id] = 0
        geo_location = GeoLocation(building["lat"], building["lon"])
        tags = [f"building={building['name']}"]
        mapCreator.nodes[location_id] = geo_location
        mapCreator.tags[location_id] = tags
        mapCreator.unconnected_nodes.add(location_id)

    mapCreator.connect_unconnected_nodes()

    cityMap = CityMap()

    for nodeLabel in mapCreator.nodes:
        cityMap.addLocation(
            nodeLabel, mapCreator.nodes[nodeLabel], tags=mapCreator.tags[nodeLabel]
        )

    for src, tgt in mapCreator.edges:
        cityMap.addConnection(src, tgt)

    if saveMap:
        path = "data/small.json" if osmPath.split("/")[-1] == "calpoly.pbf" else "data/large.json"
        cityMap.saveCityMap(path)

    return cityMap


def loadMap(large: bool = False) -> CityMap:
    cityMap = CityMap()
    filename = "./data/large.json" if large else "./data/small.json"
    cityMap.loadCityMap(filename)
    return cityMap


def printMap(cityMap: CityMap):
    for label in cityMap.geoLocations:
        tagsStr = " ".join(cityMap.tags[label])
        print(f"{label} ({cityMap.geoLocations[label]}): {tagsStr}")
        for label2, distance in cityMap.distances[label].items():
            print(f"  -> {label2} [distance = {distance}]")


def createCalPolyMap() -> CityMap:
    cityMap = readMap("data/calpoly.pbf")
    addLandmarks(cityMap, "data/calpoly-landmarks.json")
    return cityMap