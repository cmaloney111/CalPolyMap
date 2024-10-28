import heapq
from dataclasses import dataclass
from typing import Dict, Hashable, List, Optional, Tuple

@dataclass(frozen=True, order=True)
class State:
    location: str
    memory: Optional[Hashable] = None

class SearchProblem:
    def startState(self) -> State:
        raise NotImplementedError()

    def goalTest(self, state: State) -> bool:
        raise NotImplementedError()

    def successorsAndCosts(self, state: State) -> List[Tuple[str, State, float]]:
        raise NotImplementedError()

class SearchAlgorithm:
    def __init__(self):
        self.actions: List[str] = None
        self.pathCost: float = None
        self.numStatesExplored: int = 0
        self.pastCosts: Dict[str, float] = {}

    def solve(self, problem: SearchProblem) -> None:
        raise NotImplementedError()

class Heuristic:
    def evaluate(self, state: State) -> float:
        raise NotImplementedError()

class UniformCostSearch(SearchAlgorithm):
    def __init__(self, verbose: int = 0):
        super().__init__()
        self.verbose = verbose

    def solve(self, problem: SearchProblem) -> None:
        self.actions = None
        self.pathCost = None
        self.numStatesExplored = 0
        self.pastCosts = {}

        frontier = PriorityQueue()
        backpointers = {}
        startState = problem.startState()
        frontier.update(startState, 0.0)

        while True:
            state, pastCost = frontier.removeMin()
            if state is None and pastCost is None:
                if self.verbose >= 1:
                    print("Searched the entire search space!")
                return

            self.pastCosts[state.location] = pastCost
            self.numStatesExplored += 1
            if self.verbose >= 2:
                print(f"Exploring {state} with pastCost {pastCost}")

            if problem.goalTest(state):
                self.actions = []
                while state != startState:
                    action, prevState = backpointers[state]
                    self.actions.append(action)
                    state = prevState
                self.actions.reverse()
                self.pathCost = pastCost
                if self.verbose >= 1:
                    print(f"numStatesExplored = {self.numStatesExplored}")
                    print(f"pathCost = {self.pathCost}")
                    print(f"actions = {self.actions}")
                return

            for action, newState, cost in problem.successorsAndCosts(state):
                if self.verbose >= 3:
                    print(f"\t{state} => {newState} (Cost: {pastCost} + {cost})")

                if frontier.update(newState, pastCost + cost):
                    backpointers[newState] = (action, state)

class PriorityQueue:
    def __init__(self):
        self.DONE = -100000
        self.heap = []
        self.priorities = {}

    def update(self, state: State, newPriority: float) -> bool:
        oldPriority = self.priorities.get(state)
        if oldPriority is None or newPriority < oldPriority:
            self.priorities[state] = newPriority
            heapq.heappush(self.heap, (newPriority, state))
            return True
        return False

    def removeMin(self):
        while self.heap:
            priority, state = heapq.heappop(self.heap)
            if self.priorities[state] == self.DONE:
                continue
            self.priorities[state] = self.DONE
            return state, priority
        return None, None
