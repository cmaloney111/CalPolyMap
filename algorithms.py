from typing import List, Tuple

from mapUtil import (
    CityMap,
    computeDistance,
    locationFromTag,
)
from util import Heuristic, SearchProblem, State, UniformCostSearch


# *IMPORTANT* :: A key part of this assignment is figuring out how to model states
# effectively. We've defined a class `State` to help you think through this, with a
# field called `memory`.
#
# As you implement the different types of search problems below, think about what
# `memory` should contain to enable efficient search!
#   > Check out the docstring for `State` in `util.py` for more details and code.

########################################################################################
# Problem 2a: Modeling the Shortest Path Problem.


class ShortestPathProblem(SearchProblem):
    """
    Defines a search problem that corresponds to finding the shortest path
    from `startLocation` to any location with the specified `endTag`.
    """

    def __init__(self, startLocation: str, endTag: str, cityMap: CityMap):
        self.startLocation = locationFromTag(startLocation, cityMap)
        self.endTag = endTag
        self.cityMap = cityMap

    def startState(self) -> State:
        # ### START CODE HERE ###
        return State(self.startLocation)
        # ### END CODE HERE ###

    def isEnd(self, state: State) -> bool:
        # ### START CODE HERE ###
        return True if self.endTag in self.cityMap.tags[state.location] else False
        # ### END CODE HERE ###

    def successorsAndCosts(self, state: State) -> List[Tuple[str, State, float]]:
        # ### START CODE HERE ###
        succAndCost = []
        for successor in self.cityMap.distances[state.location]:
            succAndCost.append((successor, State(successor), self.cityMap.distances[state.location][successor]))
        return succAndCost
        # ### END CODE HERE ###


########################################################################################
# Problem 3a: Modeling the Waypoints Shortest Path Problem.


class WaypointsShortestPathProblem(SearchProblem):
    """
    Defines a search problem that corresponds to finding the shortest path from
    `startLocation` to any location with the specified `endTag` such that the path also
    traverses locations that cover the set of tags in `waypointTags`.

    Think carefully about what `memory` representation your States should have!
    """
    def __init__(
        self, startLocation: str, waypointTags: List[str], endTag: str, cityMap: CityMap
    ):
        self.startLocation = locationFromTag(startLocation, cityMap)
        self.endTag = endTag
        self.cityMap = cityMap

        # We want waypointTags to be consistent/canonical (sorted) and hashable (tuple)
        self.waypointTags = tuple(sorted(waypointTags))

    def startState(self) -> State:
        # ### START CODE HERE ###
        return State(self.startLocation, ())
        # ### END CODE HERE ###

    def isEnd(self, state: State) -> bool:
        # ### START CODE HERE ###
        return True if self.endTag in self.cityMap.tags[state.location] and set(self.waypointTags).issubset(state.memory) else False
        # ### END CODE HERE ###

    def successorsAndCosts(self, state: State) -> List[Tuple[str, State, float]]:
        # ### START CODE HERE ###
        succAndCost = []
        for successor in self.cityMap.distances[state.location]:
            new_mem = (set(state.memory) | set(self.cityMap.tags[successor])) & set(self.waypointTags)
            succAndCost.append((successor, State(successor, tuple(sorted(new_mem))), self.cityMap.distances[state.location][successor]))
        return succAndCost
        # ### END CODE HERE ###

########################################################################################
# Problem 4a: A* to UCS reduction

# Turn an existing SearchProblem (`problem`) you are trying to solve with a
# Heuristic (`heuristic`) into a new SearchProblem (`newSearchProblem`), such
# that running uniform cost search on `newSearchProblem` is equivalent to
# running A* on `problem` subject to `heuristic`.
#
# This process of translating a model of a problem + extra constraints into a
# new instance of the same problem is called a reduction; it's a powerful tool
# for writing down "new" models in a language we're already familiar with.


def aStarReduction(problem: SearchProblem, heuristic: Heuristic) -> SearchProblem:
    class NewSearchProblem(SearchProblem):
        def startState(self) -> State:
            # ### START CODE HERE ###
            return problem.startState()
            # ### END CODE HERE ###

        def isEnd(self, state: State) -> bool:
            # ### START CODE HERE ###
            return problem.isEnd(state)
            # ### END CODE HERE ###

        def successorsAndCosts(self, state: State) -> List[Tuple[str, State, float]]:
            # ### START CODE HERE ###
            succAndCost = []
            for successor in problem.cityMap.distances[state.location]:
                if hasattr(problem, "waypointTags"):
                    new_mem = tuple(sorted((set(state.memory) | set(problem.cityMap.tags[successor])) & set(problem.waypointTags)))
                else:
                    new_mem = None

                newCost = problem.cityMap.distances[state.location][successor] + heuristic.evaluate(State(successor)) - heuristic.evaluate(state)
                succAndCost.append((successor, State(successor, new_mem), newCost))
            return succAndCost
            # ### END CODE HERE ###

    return NewSearchProblem()


########################################################################################
# Problem 4b: "straight-line" heuristic for A*


class StraightLineHeuristic(Heuristic):
    """
    Estimate the cost between locations as the straight-line distance.
        > Hint: you might consider using `computeDistance` defined in `mapUtil.py`
    """
    def __init__(self, endTag: str, cityMap: CityMap):
        self.endTag = endTag
        self.cityMap = cityMap

        # Precompute
        # ### START CODE HERE ###
        self.endTagLocations = {}
        for location, geoLocation in cityMap.geoLocations.items():
            if endTag in cityMap.tags[location]:
                self.endTagLocations[location] = geoLocation
        # ### END CODE HERE ###

    def evaluate(self, state: State) -> float:
        # ### START CODE HERE ###
        min_dist = -1
        for location, geoLocation in self.endTagLocations.items():
            new_dist = computeDistance(geoLocation, self.cityMap.geoLocations[state.location])
            if new_dist < min_dist or min_dist == -1:
                min_dist = new_dist
        return min_dist
        # ### END CODE HERE ###


########################################################################################
# Problem 4c: "no waypoints" heuristic for A*


class NoWaypointsHeuristic(Heuristic):
    """
    Returns the minimum distance from `startLocation` to any location with `endTag`,
    ignoring all waypoints.
    """
    def __init__(self, endTag: str, cityMap: CityMap):
        """
        Precompute cost of shortest path from each location to a location with the desired endTag
        """
        # Define a reversed shortest path problem from a special END state
        # (which connects via 0 cost to all end locations) to `startLocation`.
        class ReverseShortestPathProblem(SearchProblem):
            def startState(self) -> State:
                """
                Return special "END" state
                """
                # ### START CODE HERE ###
                return State("0")
                # ### END CODE HERE ###

            def isEnd(self, state: State) -> bool:
                """
                Return False for each state.
                Because there is *not* a valid end state (`isEnd` always returns False), 
                UCS will exhaustively compute costs to *all* other states.
                """
                # ### START CODE HERE ###
                return False
                # ### END CODE HERE ###

            def successorsAndCosts(
                self, state: State
            ) -> List[Tuple[str, State, float]]:
                # If current location is the special "END" state, 
                # return all the locations with the desired endTag and cost 0 
                # (i.e, we connect the special location "END" with cost 0 to all locations with endTag)
                # Else, return all the successors of current location and their corresponding distances according to the cityMap
                # ### START CODE HERE ###
                succAndCost = []
                if state.location == "0":
                    for location in [location for location, tags in cityMap.tags.items() if endTag in tags]:
                        succAndCost.append((location, State(location, state.memory), 0))
                else:            
                    for successor in cityMap.distances[state.location]:
                        succAndCost.append((successor, State(successor), cityMap.distances[state.location][successor]))
                return succAndCost
                # ### END CODE HERE ###

        # Call UCS.solve on our `ReverseShortestPathProblem` instance. Because there is
        # *not* a valid end state (`isEnd` always returns False), will exhaustively
        # compute costs to *all* other states.
        # ### START CODE HERE ###
        self.endTag = endTag
        self.cityMap = cityMap

        ucs = UniformCostSearch(verbose=0)
        ucs.solve(ReverseShortestPathProblem())
        # ### END CODE HERE ###

        # Now that we've exhaustively computed costs from any valid "end" location
        # (any location with `endTag`), we can retrieve `ucs.pastCosts`; this stores
        # the minimum cost path to each state in our state space.
        #   > Note that we're making a critical assumption here: costs are symmetric!
        # ### START CODE HERE ###
        self.pastCosts = ucs.pastCosts
        # ### END CODE HERE ###

    def evaluate(self, state: State) -> float:
        # ### START CODE HERE ###
        return self.pastCosts[state.location]
        # ### END CODE HERE ###
    
