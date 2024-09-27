from src.utils import generate_agent_name, read_file
from src.solver import Solver
from src.setup_logger import logger


class Agent:
	"""
	Represents an Agent in the tournament.

	Each agent autoformalises a game description, plays in the tournament, and updates its state.
	It also keeps track of its payoffs, choices, and opponent's choices.
	"""

	def __init__(self, game_string, strategy="tit-for-tat"):
		"""
		Initializes the Agent with a random name, an empty payoff list, choice list, and opponent's choice list.
		"""
		self.name = generate_agent_name(3)
		self.payoffs = []  # List to store the agent's payoffs over time
		self.choices = []  # List to store the agent's choices
		self.opponent_choices = []  # List to store the opponent's choices
		# self.game = game_string
		self.strategy = strategy
		self.game = game_string
		self.solver = None
		self.valid = self.init(game_string)

	def init(self, game_string: str):
		"""
		Initializes the agent with the game.

		:return: syntactic correctness
		"""
		logger.debug(f"Agent {self.name} with strategy {self.strategy} is initializing.")
		self.game = game_string  # TODO autoformalise game description here
		solver_string = read_file("src/solver.pl")
		if self.game and solver_string:
			self.solver = Solver(solver_string, self.game)
			return self.solver.valid
		return False

	def play(self):
		"""
		The agent making a choice in the tournament.
		"""
		if self.solver:
			choice = self.solver.get_variable_value("select(p1,_,s0,M).")
			if choice:
				self.choices.append(choice)
				logger.debug(f"Agent {self.name} made choice: {choice}")
				return choice

		logger.debug(f"Agent {self.name} is not valid!")
		return None

	def update(self, opponent_choice):
		"""
		Updates the agent's payoff and logs the opponent's choice.

		:param opponent_choice: The choice made by the opponent in the current round.
		"""
		if self.solver:
			self.opponent_choices.append(opponent_choice)
			payoff = float(self.solver.get_variable_value(
				f"finally(goal(p1, U), do(choice(p1, '{self.choices[-1]}'), do(choice(p2, '{self.opponent_choices[-1]}'), s0)))."))
			self.payoffs.append(payoff)
			logger.debug(f"Agent {self.name} received payoff: {payoff} and logged opponent's choice: {opponent_choice}")
			return True
		else:
			logger.debug(f"Agent {self.name} is not valid!")
			return False

	def get_payoffs(self):
		"""
		Returns the list of payoffs accumulated by the agent.

		:return: List of payoffs.
		"""
		return self.payoffs

	def get_total_payoff(self):
		"""
		Returns the total payoff accumulated by the agent.

		:return: Total payoff.
		"""
		return sum(self.payoffs)
