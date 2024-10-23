# To test your reduction, we'll define an admissible (but fairly unhelpful) heuristic
class ZeroHeuristic(util.Heuristic):
    """Estimates the cost between locations as 0 distance."""
    def __init__(self, endTag: str, cityMap: CityMap):
        self.endTag = endTag
        self.cityMap = cityMap

    def evaluate(self, state: util.State) -> float:
        return 0.0


class Test_4a(GradedTestCase):

    def t_4a(
        self,
        cityMap: CityMap,
        startLocation: str,
        endTag: str,
        expectedCost: Optional[float] = None,
    ):
        """
        Run UCS on the A* Reduction of a ShortestPathProblem, specified by
            (startLocation, endTag).
        """
        # We'll use the ZeroHeuristic to verify that the reduction works as expected
        zeroHeuristic = ZeroHeuristic(endTag, cityMap)

        # Define the baseProblem and corresponding reduction (using `zeroHeuristic`)
        baseProblem = algorithms.ShortestPathProblem(startLocation, endTag, cityMap)
        aStarProblem = algorithms.aStarReduction(baseProblem, zeroHeuristic)

        # Solve the reduction via a call to `ucs.solve` (similar to prior tests)
        ucs = util.UniformCostSearch(verbose=0)
        ucs.solve(aStarProblem)
        path = extractPath(startLocation, ucs)
        self.assertTrue(checkValid(path, cityMap, startLocation, endTag, []))
        if expectedCost is not None:
            self.assertEqual(expectedCost, getTotalCost(path, cityMap))

        # BEGIN_HIDE
        # END_HIDE

    @graded(timeout=1)
    def test_0(self):
        """4a-0-basic: A* shortest path on small grid."""

        self.t_4a(
            cityMap=createGridMap(3, 5),
            startLocation=makeGridLabel(0, 0),
            endTag=makeTag("label", makeGridLabel(2, 2)),
            expectedCost=4,
        )

    @graded(timeout=1)
    def test_1(self):
        """4a-1-basic: A* shortest path with multiple end locations."""

        self.t_4a(
            cityMap=createGridMap(30, 30),
            startLocation=makeGridLabel(20, 10),
            endTag=makeTag("x", "5"),
            expectedCost=15,
        )

    @graded(timeout=2, is_hidden=True)
    def test_2(self):
        """4a-2-hidden: A* shortest path with larger grid."""

        self.t_4a(
            cityMap=createGridMap(100, 100),
            startLocation=makeGridLabel(0, 0),
            endTag=makeTag("label", makeGridLabel(99, 99)),
        )
        
class Test_4b(GradedTestCase):

    def setUp(self):

        # Initialize a `StraightLineHeuristic` using `endTag3b` and the `stanfordMap`
        self.endTag3b = makeTag("landmark", "gates")

        try:
            self.stanfordStraightLineHeuristic = algorithms.StraightLineHeuristic(
                self.endTag3b, stanfordMap
            )
        except:
            self.stanfordStraightLineHeuristic = None
        

    def t_4b_heuristic(
        self,
        cityMap: CityMap,
        startLocation: str,
        endTag: str,
        expectedCost: Optional[float] = None,
    ):
        """Targeted test for `StraightLineHeuristic` to ensure correctness."""
        heuristic = algorithms.StraightLineHeuristic(endTag, cityMap)
        heuristicCost = heuristic.evaluate(util.State(startLocation))
        if expectedCost is not None:
            self.assertEqual(expectedCost, heuristicCost)

        # BEGIN_HIDE
        # END_HIDE
            
    @graded(timeout=1)
    def test_0(self):
        """4b-0-basic: basic straight line heuristic unit test."""

        self.t_4b_heuristic(
            cityMap=createGridMap(3, 5),
            startLocation=makeGridLabel(0, 0),
            endTag=makeTag("label", makeGridLabel(2, 2)),
            expectedCost=3.145067466556296,
        )

    @graded(timeout=1, is_hidden=True)
    def test_1(self):
        """4b-1-hidden: hidden straight line heuristic unit test."""

        self.t_4b_heuristic(
            cityMap=createGridMap(100, 100),
            startLocation=makeGridLabel(0, 0),
            endTag=makeTag("label", makeGridLabel(99, 99)),
        )

    def t_4b_aStar(
        self,
        startLocation: str, 
        heuristic: util.Heuristic, 
        expectedCost: Optional[float] = None
    ):
        """Run UCS on the A* Reduction of a ShortestPathProblem, w/ `heuristic`"""
        baseProblem = algorithms.ShortestPathProblem(startLocation, self.endTag3b, stanfordMap)
        aStarProblem = algorithms.aStarReduction(baseProblem, heuristic)

        # Solve the reduction via a call to `ucs.solve` (similar to prior tests)
        ucs = util.UniformCostSearch(verbose=0)
        ucs.solve(aStarProblem)
        path = extractPath(startLocation, ucs)
        self.assertTrue(checkValid(path, stanfordMap, startLocation, self.endTag3b, []))
        if expectedCost is not None:
            self.assertEqual(expectedCost, getTotalCost(path, stanfordMap))

        # BEGIN_HIDE
        # END_HIDE
            
    @graded(timeout=2)
    def test_2(self):
        """4b-2-basic: basic straight line heuristic A* on Stanford map (4b-astar-1)."""

        self.t_4b_aStar(
            startLocation=locationFromTag(makeTag("landmark", "oval"), stanfordMap),
            heuristic=self.stanfordStraightLineHeuristic,
            expectedCost=446.9972442143235,
        )

    @graded(timeout=2)
    def test_3(self):
        """4b-3-basic: basic straight line heuristic A* on Stanford map (4b-astar-2)."""

        self.t_4b_aStar(
            startLocation=locationFromTag(makeTag("landmark", "rains"), stanfordMap),
            heuristic=self.stanfordStraightLineHeuristic,
            expectedCost=2005.4388573303765,
        )

    @graded(timeout=2, is_hidden=True)
    def test_4(self):
        """4b-4-hidden: hidden straight line heuristic A* on Stanford map (4b-astar-3)."""

        self.t_4b_aStar(
            startLocation=locationFromTag(makeTag("landmark", "bookstore"), stanfordMap),
            heuristic=self.stanfordStraightLineHeuristic,
        )

    @graded(timeout=2, is_hidden=True)
    def test_5(self):
        """4b-5-hidden: hidden straight line heuristic A* on Stanford map (4b-astar-4)."""

        self.t_4b_aStar(
            startLocation=locationFromTag(makeTag("landmark", "evgr_a"), stanfordMap),
            heuristic=self.stanfordStraightLineHeuristic,
        )

class Test_4c(GradedTestCase):

    def setUp(self):

        self.endTag3c = makeTag("wheelchair", "yes")

        try:
            self.stanfordNoWaypointsHeuristic = algorithms.NoWaypointsHeuristic(
                self.endTag3c, stanfordMap
            )
        except:
            self.stanfordNoWaypointsHeuristic = None

    def t_4c_heuristic(
        self,
        startLocation: str, 
        endTag: str, 
        expectedCost: Optional[float] = None
    ):
        """Targeted test for `NoWaypointsHeuristic` -- uses the full Stanford map."""
        heuristic = algorithms.NoWaypointsHeuristic(endTag, stanfordMap)
        heuristicCost = heuristic.evaluate(util.State(startLocation))
        if expectedCost is not None:
            self.assertEqual(expectedCost, heuristicCost)

        # BEGIN_HIDE
        # END_HIDE
            
    @graded(timeout=2)
    def test_0(self):
        """4c-0-basic: basic no waypoints heuristic unit test."""

        self.t_4c_heuristic(
            startLocation=locationFromTag(makeTag("landmark", "oval"), stanfordMap),
            endTag=makeTag("landmark", "gates"),
            expectedCost=446.99724421432353,
        )

    @graded(timeout=2, is_hidden=True)
    def test_1(self):
        """4c-1-hidden: hidden no waypoints heuristic unit test w/ multiple end locations."""

        self.t_4c_heuristic(
            startLocation=locationFromTag(makeTag("landmark", "bookstore"), stanfordMap),
            endTag=makeTag("amenity", "food"),
        )

    def t_4c_aStar(
        self,
        startLocation: str,
        waypointTags: List[str],
        heuristic: util.Heuristic,
        expectedCost: Optional[float] = None,
    ):
        """Run UCS on the A* Reduction of a WaypointsShortestPathProblem, w/ `heuristic`"""
        baseProblem = algorithms.WaypointsShortestPathProblem(
            startLocation, waypointTags, self.endTag3c, stanfordMap
        )
        aStarProblem = algorithms.aStarReduction(baseProblem, heuristic)

        # Solve the reduction via a call to `ucs.solve` (similar to prior tests)
        ucs = util.UniformCostSearch(verbose=0)
        ucs.solve(aStarProblem)
        path = extractPath(startLocation, ucs)
        self.assertTrue(
            checkValid(path, stanfordMap, startLocation, self.endTag3c, waypointTags)
        )
        if expectedCost is not None:
            self.assertEqual(expectedCost, getTotalCost(path, stanfordMap))

        # BEGIN_HIDE
        # END_HIDE

    @graded(timeout=2)
    def test_2(self):
        """4c-2-basic: basic no waypoints heuristic A* on Stanford map (4c-astar-1)."""

        self.t_4c_aStar(
            startLocation=locationFromTag(makeTag("landmark", "oval"), stanfordMap),
            waypointTags=[
                makeTag("landmark", "gates"),
                makeTag("landmark", "AOERC"),
                makeTag("landmark", "bookstore"),
                makeTag("landmark", "hoover_tower"),
            ],
            heuristic=self.stanfordNoWaypointsHeuristic,
            expectedCost=2943.242598551967,
        )

    @graded(timeout=2)
    def test_3(self):
        """4c-3-basic: basic no waypoints heuristic A* on Stanford map (4c-astar-1)."""

        self.t_4c_aStar(
            startLocation=locationFromTag(makeTag("landmark", "AOERC"), stanfordMap),
            waypointTags=[
                makeTag("landmark", "tressider"),
                makeTag("landmark", "hoover_tower"),
                makeTag("amenity", "food"),
            ],
            heuristic=self.stanfordNoWaypointsHeuristic,
            expectedCost=1677.3814380413373,
        )

    @graded(timeout=10, is_hidden=True)
    def test_4(self):
        """4c-4-hidden: hidden no waypoints heuristic A* on Stanford map (4c-astar-3)."""

        self.t_4c_aStar(
            startLocation=locationFromTag(makeTag("landmark", "tressider"), stanfordMap),
            waypointTags=[
                makeTag("landmark", "gates"),
                makeTag("amenity", "food"),
                makeTag("landmark", "rains"),
                makeTag("landmark", "stanford_stadium"),
                makeTag("bicycle", "yes"),
            ],
            heuristic=self.stanfordNoWaypointsHeuristic,
        )
