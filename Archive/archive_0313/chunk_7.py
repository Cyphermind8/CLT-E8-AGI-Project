# Chunk 7: Reinforcement Learning - Q-Learning Algorithm

import numpy as np
import random

class QLearningAgent:
    """A simple Q-learning agent that learns to navigate a grid environment."""
    def __init__(self, grid_size, learning_rate=0.1, discount_factor=0.9, exploration_rate=1.0, exploration_decay=0.99):
        self.grid_size = grid_size
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.exploration_rate = exploration_rate
        self.exploration_decay = exploration_decay

        # Initialize Q-table with zeros
        self.q_table = np.zeros((grid_size, grid_size, 4))  # 4 possible actions (up, down, left, right)

    def choose_action(self, state):
        """Choose an action based on exploration-exploitation strategy."""
        if random.uniform(0, 1) < self.exploration_rate:
            return random.choice(range(4))  # Explore: Random action
        return np.argmax(self.q_table[state[0], state[1]])  # Exploit: Best known action

    def update_q_value(self, state, action, reward, next_state):
        """Update the Q-table using the Q-learning formula."""
        best_next_action = np.argmax(self.q_table[next_state[0], next_state[1]])
        target = reward + self.discount_factor * self.q_table[next_state[0], next_state[1], best_next_action]
        self.q_table[state[0], state[1], action] += self.learning_rate * (target - self.q_table[state[0], state[1], action])

    def train(self, episodes, environment):
        """Train the agent over multiple episodes."""
        for episode in range(episodes):
            state = environment.reset()
            done = False

            while not done:
                action = self.choose_action(state)
                next_state, reward, done = environment.step(state, action)
                self.update_q_value(state, action, reward, next_state)
                state = next_state

            # Decay exploration rate
            self.exploration_rate *= self.exploration_decay

class GridEnvironment:
    """A simple grid environment where an agent learns to reach a goal."""
    def __init__(self, size):
        self.size = size
        self.goal = (size-1, size-1)  # Goal position
        self.walls = [(1, 1), (2, 2), (3, 1)]  # Walls in the environment

    def reset(self):
        """Reset the environment to the start state."""
        return (0, 0)  # Starting position

    def step(self, state, action):
        """Move the agent and return the new state, reward, and done flag."""
        x, y = state
        if action == 0:  # Up
            x = max(0, x - 1)
        elif action == 1:  # Down
            x = min(self.size - 1, x + 1)
        elif action == 2:  # Left
            y = max(0, y - 1)
        elif action == 3:  # Right
            y = min(self.size - 1, y + 1)

        next_state = (x, y)

        # Check if the agent hit a wall
        if next_state in self.walls:
            return state, -1, False  # Penalize hitting a wall

        # Check if the agent reached the goal
        if next_state == self.goal:
            return next_state, 10, True  # Reward for reaching goal

        return next_state, -0.1, False  # Small penalty for each step

def q_learning_example():
    """Example usage of Q-learning for AI decision-making."""
    grid_size = 5
    environment = GridEnvironment(grid_size)
    agent = QLearningAgent(grid_size)

    print("Training agent on the grid environment...")
    agent.train(episodes=1000, environment=environment)
    print("Training complete! AI has learned the optimal path.")

# Example usage
q_learning_example()
