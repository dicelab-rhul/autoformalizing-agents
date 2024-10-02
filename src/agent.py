from src.game import Game
from src.utils import generate_agent_name, read_file
from src.solver import Solver
from src.setup_logger import logger
from src.utils import read_file, parse_axioms
from llms.gpt4 import GPT4
import os


class Agent:
	"""
	Represents an Agent in the tournament.

	Each agent autoformalises a game description, plays in the tournament, and updates its state.
	It also keeps track of its payoffs, choices, and opponent's choices.
	"""

	def __init__(self, game_string, strategy_path="tit-for-tat", solver_path="src/solver.pl", prompt_path="DATA/PROMPTS/prompt_template.txt"):
		"""
		Initializes the Agent with a random name, an empty payoff list, choice list, and opponent's choice list.
		"""
		self.name = generate_agent_name(3)
		self.payoffs = []  # List to store the agent's payoffs over time
		self.choices = []  # List to store the agent's choices
		self.opponent_choices = []  # List to store the opponent's choices

		self.game = Game(game_string)  # Game information object
		self.strategy_name = strategy_path.split(os.sep)[-1][:-3]
		self.strategy = read_file(strategy_path)  # Strategy

		self.solver_path = solver_path  # Path to domain-independent solver
		self.prompt_path = prompt_path  # Path to prompt template

		self.solver = None  # Solver object
		self.llm = GPT4()

		self.valid = self.init()

	def init(self):
		"""
		Initializes the agent with the game.

		:return: syntactic correctness
		"""
		logger.debug(f"Agent {self.name} with strategy {self.strategy_name} is initializing.")
		prompt = read_file(self.prompt_path)
		prompt = prompt.replace('{game_description}', self.game.game_string)
		response = self.llm.prompt(prompt)

		try:
			game_rules = parse_axioms(response)
			self.game.set_rules(game_rules)
		except ValueError:
			# TODO instruction following error ('@' not added)
			logger.debug(f"Agent {self.name} experienced instruction following error!")
			return False

		solver_string = read_file(self.solver_path)
		if self.game and solver_string:
			self.solver = Solver(solver_string, self.game.game_rules, self.strategy)
			# TODO if not valid syntactic error
			return self.solver.valid
		return False

	def play(self):
		"""
		The agent making a choice in the tournament.
		"""
		if self.solver:
			choices = self.solver.get_variable_value("select(p1,_,s0,M).")
			if choices:
				choice = next(iter(choices[0].values()))
				self.choices.append(choice)
				logger.debug(f"Agent {self.name} made choice: {choice}")
				return choice

		logger.debug(f"Agent {self.name} is not valid!")
		# TODO runtime error
		return None

	def update(self, opponent_choice):
		"""
		Updates the agent's payoff and logs the opponent's choice.

		:param opponent_choice: The choice made by the opponent in the current round.
		"""
		if self.solver:
			self.opponent_choices.append(opponent_choice)
			payoffs = self.solver.get_variable_value(
				f"finally(goal(p1, U), do(choice(p1, '{self.choices[-1]}'), do(choice(p2, '{self.opponent_choices[-1]}'), s0))).")
			if payoffs:
				payoff = float(next(iter(payoffs[0].values())))
				self.payoffs.append(payoff)
				logger.debug(f"Agent {self.name} received payoff: {payoff} and logged opponent's choice: {opponent_choice}")
				# TODO update the opponent move in Prolog
				return True
			else:
				return False
		else:
			logger.debug(f"Agent {self.name} is not valid!")
			# TODO runtime error
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
