# Chunk 8: Genetic Algorithm for AI Optimization

import random

class Individual:
    """Represents an individual in the genetic algorithm population."""
    def __init__(self, chromosome_length):
        self.chromosome = [random.randint(0, 1) for _ in range(chromosome_length)]
        self.fitness = self.calculate_fitness()

    def calculate_fitness(self):
        """Fitness function: Number of 1s in the chromosome (for simplicity)."""
        return sum(self.chromosome)

    def mutate(self, mutation_rate):
        """Mutates the individual by flipping random bits."""
        for i in range(len(self.chromosome)):
            if random.uniform(0, 1) < mutation_rate:
                self.chromosome[i] = 1 - self.chromosome[i]  # Flip bit

def crossover(parent1, parent2):
    """Performs single-point crossover between two parents."""
    crossover_point = random.randint(1, len(parent1.chromosome) - 1)
    child1 = Individual(len(parent1.chromosome))
    child2 = Individual(len(parent2.chromosome))

    child1.chromosome = parent1.chromosome[:crossover_point] + parent2.chromosome[crossover_point:]
    child2.chromosome = parent2.chromosome[:crossover_point] + parent1.chromosome[crossover_point:]

    return child1, child2

class GeneticAlgorithm:
    """Implements a simple genetic algorithm for optimization."""
    def __init__(self, population_size, chromosome_length, mutation_rate, generations):
        self.population_size = population_size
        self.chromosome_length = chromosome_length
        self.mutation_rate = mutation_rate
        self.generations = generations
        self.population = [Individual(chromosome_length) for _ in range(population_size)]

    def evolve(self):
        """Evolves the population over multiple generations."""
        for generation in range(self.generations):
            self.population.sort(key=lambda x: x.fitness, reverse=True)
            next_generation = self.population[:self.population_size // 2]  # Select top half

            # Crossover to create new children
            while len(next_generation) < self.population_size:
                parent1, parent2 = random.sample(next_generation, 2)
                child1, child2 = crossover(parent1, parent2)
                next_generation.extend([child1, child2])

            # Mutate new generation
            for individual in next_generation:
                individual.mutate(self.mutation_rate)

            self.population = next_generation

        # Return best individual from final generation
        best_individual = max(self.population, key=lambda x: x.fitness)
        return best_individual

def genetic_algorithm_example():
    """Example usage of a genetic algorithm for optimization."""
    ga = GeneticAlgorithm(population_size=20, chromosome_length=10, mutation_rate=0.1, generations=50)
    best_solution = ga.evolve()
    print("Best solution found:", best_solution.chromosome, "Fitness:", best_solution.fitness)

# Example usage
genetic_algorithm_example()
