# Chunk 6: AI-Based Pathfinding Algorithm (A* Search)

import heapq

class Node:
    """Represents a node in the grid for pathfinding."""
    def __init__(self, position, parent=None):
        self.position = position
        self.parent = parent
        self.g = 0  # Distance from start node
        self.h = 0  # Heuristic estimate to end node
        self.f = 0  # Total cost (g + h)

    def __lt__(self, other):
        return self.f < other.f

def heuristic(a, b):
    """Calculate the Manhattan distance heuristic."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def astar_search(grid, start, end):
    """Finds the shortest path in a grid using the A* algorithm."""
    open_list = []
    closed_set = set()
    start_node = Node(start)
    end_node = Node(end)

    heapq.heappush(open_list, start_node)

    while open_list:
        current_node = heapq.heappop(open_list)
        closed_set.add(current_node.position)

        # If we reached the goal, reconstruct the path
        if current_node.position == end_node.position:
            path = []
            while current_node:
                path.append(current_node.position)
                current_node = current_node.parent
            return path[::-1]  # Return reversed path

        neighbors = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # Right, Down, Left, Up
        for dx, dy in neighbors:
            neighbor_pos = (current_node.position[0] + dx, current_node.position[1] + dy)

            # Check if neighbor is within grid bounds
            if 0 <= neighbor_pos[0] < len(grid) and 0 <= neighbor_pos[1] < len(grid[0]):
                if grid[neighbor_pos[0]][neighbor_pos[1]] == 1 or neighbor_pos in closed_set:
                    continue  # Ignore walls and already visited nodes

                neighbor_node = Node(neighbor_pos, current_node)
                neighbor_node.g = current_node.g + 1
                neighbor_node.h = heuristic(neighbor_pos, end_node.position)
                neighbor_node.f = neighbor_node.g + neighbor_node.h

                if any(node.position == neighbor_pos and node.f <= neighbor_node.f for node in open_list):
                    continue  # Ignore if a better path already exists

                heapq.heappush(open_list, neighbor_node)

    return None  # No path found

def astar_example():
    """Example usage of A* search algorithm for AI pathfinding."""
    grid = [
        [0, 0, 0, 0, 0],
        [0, 1, 1, 1, 0],
        [0, 0, 0, 1, 0],
        [0, 1, 0, 0, 0],
        [0, 0, 0, 0, 0]
    ]  # 0 = Open path, 1 = Wall

    start = (0, 0)  # Start position
    end = (4, 4)  # Goal position

    path = astar_search(grid, start, end)
    if path:
        print("Shortest path found:", path)
    else:
        print("No path found.")

# Example usage
astar_example()
