import math
import random

def create_inital_population(population_size, cities):
    inital_population = []
    for i in range(population_size):
        individual = random.sample(cities, len(cities))
        inital_population.append(individual)
    return inital_population


def select_parents(population, fitness_scores):
    total_fitness = sum(fitness_scores)
    pick = random.uniform(0, total_fitness)
    current = 0
    for i, score in enumerate(fitness_scores):
        current += score
        if current > pick:
            return population[i]


def calculate_distance(city1, city2):
    return math.sqrt((city1[0] - city2[0])**2 + (city1[1] - city2[1])**2 + (city1[2] - city2[2])**2)


def crossover(parent1, parent2):
    # this function will help create a child of two parents such that the positions are jumbled
    start, end = sorted(random.sample(range(len(parent1)), 2))
    child = [None] * len(parent1)
    # copy the randomly selected two pointer in parent1 and copy it and then copy reming from parent 2
    child[start: end+1]= parent1[start:end+1]
    vacant_position=0
    for city in parent2:
        if city not in child:
            # iterate till i get a vacant position
            while child[vacant_position] is not None:
                vacant_position += 1
            child[vacant_position] = city
    return child 


def calculate_fitness(path):
    total_distance = 0
    for i in range(len(path)-1):
        total_distance+= calculate_distance(path[i], path[i+1])
    # adding the last city to first as we want to return to first city
    total_distance+= calculate_distance(path[-1], path[0])
    return total_distance


def mutate(path, mutation_rate):
    # this function swaps some cities according to the mutation rate for more versatile genes
    if random.random() < mutation_rate:
        i, j = random.sample(range(len(path)), 2)
        path[i], path[j] = path[j], path[i]
    return path


def generate_next_population(population, cities, elite_fraction, mutation_rate):
    fitness_scores = []
    for path in population:
        fitness_scores.append(1/calculate_fitness(path))
    next_population = []
    # extracting elite genes count from elite fraction to directly consider as they are the best genes from current population
    elite_count = int(len(population) * elite_fraction)
    # sort the population so we can directly take the first elite count genes
    sorted_population = []
    zipped = list(zip(fitness_scores,population))
    # sort the zipped list which has fitness
    zipped.sort(key=lambda x:x[0], reverse=True)
    for i, path in zipped:
        sorted_population.append(path)
    # directly append first elite genes from current population
    next_population.extend(sorted_population[:elite_count])
    while len(next_population) < len(population):
        parent1 = select_parents(population, fitness_scores)
        parent2 = select_parents(population, fitness_scores)
        child = crossover(parent1, parent2)
        child = mutate(child, mutation_rate)
        next_population.append(child)
    return next_population



def genetic_algorithm(cities, generations, population_size, elite_fraction, mutation_rate):
    population = create_inital_population(population_size, cities) # rather than passing the whole cities list I am dealing with index to reduce overhead and improve speed
    best_distance = float('inf')
    best_path = None
    # run a loop for specifies generations to get the best output
    for generation in range(generations):
        fitness_scores = []
        for path in population:
            fitness_scores.append(1/calculate_fitness(path))
        best_generation_index = fitness_scores.index(max(fitness_scores)) # here we find max because we inversed the distance in finding fitness so bigger the fitness smaller the distance
        best_generation_distance = calculate_fitness(population[best_generation_index]) # retrieving the distance of the best path
        if best_generation_distance < best_distance:
            best_distance = best_generation_distance
            best_path = population[best_generation_index]
        population = generate_next_population(population, cities, elite_fraction, mutation_rate)
    return best_distance, best_path



if __name__=="__main__":
    # extracting input data
    with open("input.txt","r") as f:
        input_data = f.read().splitlines()
    n = int(input_data[0]) # first line contains the number of cities
    cities = []
    for line in input_data[1:n+1]:
        cities.append(tuple(map(int, line.split())))
    # Specifying hyperparameters
    generations = 300
    if n<50:
        generations = 1500
    elif n<100:
        generations = 2000
    elif n<200:
        generations = 2250
    else:
        generations = 600
    population_size = 25
    elite_fraction = 0.2
    mutation_rate = 0.05

    # calling the genetic algorithm function
    best_distance, best_path = genetic_algorithm(cities, generations, population_size, elite_fraction, mutation_rate)
    
    # put the output in output file
    with open("output.txt", "w") as f:
        f.write(f"{best_distance:.3f}\n")
        for city in best_path:
            f.write(" ".join(map(str, city)) + "\n")
        f.write(" ".join(map(str, best_path[0])) + "\n")