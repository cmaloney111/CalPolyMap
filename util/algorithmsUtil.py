from typing import List, Tuple

from util.mapUtil import (
    CityMap,
    computeDistance,
    locationFromTag,
)
from util.generalUtil import Heuristic, SearchProblem, State, UniformCostSearch

class ShortestPathProblem(SearchProblem):
    def __init__(self, startLocation: str, endTag: str, cityMap: CityMap):
        self.startLocation = locationFromTag(startLocation, cityMap)
        self.endTag = endTag
        self.cityMap = cityMap

    def startState(self) -> State:
        return State(self.startLocation)

    def goalTest(self, state: State) -> bool:
        return self.endTag in self.cityMap.tags[state.location]

    def successorsAndCosts(self, state: State) -> List[Tuple[str, State, float]]:
        succAndCost = []
        for successor in self.cityMap.distances[state.location]:
            succAndCost.append((successor, State(successor), self.cityMap.distances[state.location][successor]))
        return succAndCost


class WaypointsShortestPathProblem(SearchProblem):
    def __init__(
        self, startLocation: str, waypointTags: List[str], endTag: str, cityMap: CityMap
    ):
        print(startLocation)
        print(waypointTags)
        self.startLocation = locationFromTag(startLocation, cityMap)
        self.endTag = endTag
        self.cityMap = cityMap

        self.waypointTags = tuple(sorted(waypointTags))
        print(waypointTags)

    def startState(self) -> State:
        return State(self.startLocation, ())
        
    def goalTest(self, state: State) -> bool:
        return self.endTag in self.cityMap.tags[state.location] and set(self.waypointTags).issubset(state.memory)
        

    def successorsAndCosts(self, state: State) -> List[Tuple[str, State, float]]:
        succAndCost = []
        for successor in self.cityMap.distances[state.location]:
            new_mem = (set(state.memory) | set(self.cityMap.tags[successor])) & set(self.waypointTags)
            succAndCost.append((successor, State(successor, tuple(sorted(new_mem))), self.cityMap.distances[state.location][successor]))
        return succAndCost
        


def aStarReduction(problem: SearchProblem, heuristic: Heuristic) -> SearchProblem:
    class NewSearchProblem(SearchProblem):
        def startState(self) -> State:   
            return problem.startState()
            
        def goalTest(self, state: State) -> bool:   
            return problem.goalTest(state)
            
        def successorsAndCosts(self, state: State) -> List[Tuple[str, State, float]]:  
            succAndCost = []
            for successor in problem.cityMap.distances[state.location]:
                if hasattr(problem, "waypointTags"):
                    new_mem = tuple(sorted((set(state.memory) | set(problem.cityMap.tags[successor])) & set(problem.waypointTags)))
                else:
                    new_mem = None
                newCost = problem.cityMap.distances[state.location][successor] + heuristic.evaluate(state=State(successor)) - heuristic.evaluate(state=state)
                succAndCost.append((successor, State(successor, new_mem), newCost))
            return succAndCost
            
    return NewSearchProblem()


class Zero(Heuristic):
    def __init__(self, endTag: str, cityMap: CityMap):
        self.endTag = endTag
        self.cityMap = cityMap

    def evaluate(self, state: State) -> float:
        return 0.0


class Geodesic(Heuristic):
    def __init__(self, endTag: str, cityMap: CityMap):
        self.endTag = endTag
        self.cityMap = cityMap
        self.endTagLocations = {}
        for location, geoLocation in cityMap.geoLocations.items():
            if endTag in cityMap.tags[location]:
                self.endTagLocations[location] = geoLocation
        
    def evaluate(self, state: State) -> float:
        min_dist = -1
        for location, geoLocation in self.endTagLocations.items():
            new_dist = computeDistance(geoLocation, self.cityMap.geoLocations[state.location])
            if new_dist < min_dist or min_dist == -1:
                min_dist = new_dist
        return min_dist
        

class NoWaypoints(Heuristic):
    def __init__(self, endTag: str, cityMap: CityMap):
        # Precompute cost of shortest path from each location to a location with the desired endTag  
        class ReverseShortestPathProblem(SearchProblem):
            def startState(self) -> State:
                # Special end state
                return State("0")   

            def goalTest(self, state: State) -> bool:
                # Compute cost to all other states (no end state)
                return False
                
            def successorsAndCosts(self, state: State) -> List[Tuple[str, State, float]]:
                succAndCost = []
                if state.location == "0":
                    for location in [location for location, tags in cityMap.tags.items() if endTag in tags]:
                        succAndCost.append((location, State(location, state.memory), 0))
                else:            
                    for successor in cityMap.distances[state.location]:
                        succAndCost.append((successor, State(successor), cityMap.distances[state.location][successor]))
                return succAndCost
            
        self.endTag = endTag
        self.cityMap = cityMap
        ucs = UniformCostSearch(verbose=0)
        ucs.solve(ReverseShortestPathProblem())
        self.pastCosts = ucs.pastCosts
        
    def evaluate(self, state: State) -> float:
        return self.pastCosts[state.location]
        
    
