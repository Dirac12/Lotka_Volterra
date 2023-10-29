from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from mesa.visualization.UserParam import UserSettableParameter
import random

class Prey(Agent):
    def __init__(self, unique_id, model, age, reproduction_rate):
        super().__init__(unique_id, model)
        self.age = age
        self.reproduction_rate = reproduction_rate
        self.growth = False

    def move(self):
        print('grid', self.model.grid)
        possible_moves = self.model.grid.get_neighborhood(
            self.pos,
            moore=True,
            include_center=False
        )
        new_position = self.random.choice(possible_moves)
        self.model.grid.move_agent(self, new_position)

    def step(self):
        print('step', self.pos)
        self.move()
        self.age += 1
        if self.age >= 12:
            self.growth = True
            self.reproduce()

    def reproduce(self):
        if self.growth:
            possible_moves = self.model.grid.get_neighborhood(
                self.pos,
                moore=True,
                include_center=False
            )
            empty_neighbors = [cell for cell in possible_moves if self.model.grid.is_cell_empty(cell)]
            if empty_neighbors:
                new_position = self.random.choice(empty_neighbors)
                new_prey = Prey(self.model.next_id(), self.model, age=0, reproduction_rate=self.reproduction_rate)
                self.model.grid.place_agent(new_prey, new_position)
                self.model.schedule.add(new_prey)

class Predator(Agent):
    def __init__(self, unique_id, model, age, reproduction_rate):
        super().__init__(unique_id, model)
        self.age = age
        self.reproduction_rate = reproduction_rate
        self.satiation = 0

    def move(self):
        possible_moves = self.model.grid.get_neighborhood(
            self.pos,
            moore=True,
            include_center=False
        )
        new_position = self.random.choice(possible_moves)

        self.satiation -= 1

        if self.model.grid.is_cell_empty(new_position):
            self.model.grid.move_agent(self, new_position)
        else:
            cellmates = self.model.grid.get_cell_list_contents([new_position])
            for mate in cellmates:
                if isinstance(mate, Prey):
                    self.satiation += 10
                    self.model.grid.remove_agent(mate)
                else:
                    pass

        if self.satiation <= 0:
            self.model.grid.remove_agent(self)

    def step(self):
        self.move()
        self.age += 1
        if self.age >= 15:
            self.reproduce()

    def reproduce(self):
        if self.age >= self.reproduction_rate:
            possible_moves = self.model.grid.get_neighborhood(
                self.pos,
                moore=True,
                include_center=False
            )
            empty_neighbors = [cell for cell in possible_moves if self.model.grid.is_cell_empty(cell)]
            if empty_neighbors:
                new_position = self.random.choice(empty_neighbors)
                new_predator = Predator(self.model.next_id(), self.model, age=0, reproduction_rate=self.reproduction_rate)
                self.model.grid.place_agent(new_predator, new_position)
                self.model.schedule.add(new_predator)

class Environment(MultiGrid):
    pass

class PopulationModel(Model):
    def __init__(self, width, height, num_prey, num_predators, prey_reproduction_rate, predator_reproduction_rate):
        super().__init__()
        self.schedule = RandomActivation(self)
        self.grid = Environment(width, height, True)
        self.num_prey = num_prey
        self.num_predators = num_predators
        self.prey_reproduction_rate = prey_reproduction_rate
        self.predator_reproduction_rate = predator_reproduction_rate

        # Create prey agents
        for i in range(self.num_prey):
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            prey = Prey(self.next_id(), self, age=0, reproduction_rate=self.prey_reproduction_rate)
            self.grid.place_agent(prey, (x, y))
            self.schedule.add(prey)

        # Create predator agents
        for i in range(self.num_predators):
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            predator = Predator(self.next_id(), self, age=0, reproduction_rate=self.predator_reproduction_rate)
            self.grid.place_agent(predator, (x, y))
            self.schedule.add(predator)

    def step(self):
        self.schedule.step()

def agent_portrayal(agent):
    portrayal = { "Shape": "circle",
                  "Color": "grey",
                  "Filled":"true",
                  "Layer": 0,
                  "r": 0.75}
    if agent.reproduction_rate:
        portrayal["Color"] = "LimeGreen"
        portrayal["Layer"] = 1
    return portrayal
    if agent.age:
        portrayal["Color"] = "Red"
        portrayal["Layer"] = 1
    return portrayal
params = {
    "num_prey": UserSettableParameter('slider', 'Number of Prey', 100, 10, 300),
    "num_predators": UserSettableParameter('slider', 'Number of Predators', 50, 10, 300),
    "prey_reproduction_rate": UserSettableParameter('slider', 'Prey Reproduction Rate', 10, 1, 50),
    "predator_reproduction_rate": UserSettableParameter('slider', 'Predator Reproduction Rate', 5, 1, 30),
    "width": 50,
    "height": 40
}

grid = CanvasGrid(agent_portrayal, params["width"], params["height"], 500, 400)
server = ModularServer(PopulationModel, [grid], "Population Model", params)
server.launch()

