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

	def __init__(self, game_string="", strategy_path="tit-for-tat", solver_path="src/solver.pl",
				 prompt_path="DATA/PROMPTS/prompt_template.txt", game_path=""):
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
		self.default_move = None
		self.player_name = None # TODO get names
		self.opponent_name = None

		self.solver_path = solver_path  # Path to domain-independent solver
		self.prompt_path = prompt_path  # Path to prompt template

		self.solver = None  # Solver object
		self.llm = GPT4()

		self.valid = self.init(game_path)

	def init(self, game_rules_path=""):
		"""
		Initializes the agent with the game.

		:return: syntactic correctness
		"""
		logger.debug(f"Agent {self.name} with strategy {self.strategy_name} is initializing.")

		if game_rules_path=="":
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
		else:
			game_rules = read_file(os.path.normpath(game_rules_path))
			self.game.set_rules(game_rules)

		solver_string = read_file(self.solver_path)
		if self.game and solver_string:
			self.solver = Solver(solver_string, self.game.game_rules, self.strategy)
			if self.solver:
				default_move = self.solver.get_variable_values("initially(default_move(_, X), s0).", 1)
				possible_moves = self.solver.get_variable_values("possible(choice(_,X), s0).")
				player_names = self.solver.get_variable_values("holds(player(N), s0).")
				if default_move and possible_moves and player_names:
					self.game.set_possible_moves(set(possible_moves))
					self.default_move = default_move[0]
					self.player_name = player_names[0]
					self.opponent_name = player_names[1]
					self.game.set_players(player_names)
					logger.debug(f"Agent {self.name} has possible choices {self.game.get_possible_moves()} and default"
								 f" move {self.default_move}. The player name is {self.player_name} "
								 f"and the opponent name is {self.opponent_name}.")
				else:
					return False
			# TODO if not valid syntactic error
			return self.solver.valid
		return False

	# TODO set default move method

	def play(self):
		"""
		The agent making a choice in the tournament.
		"""
		if self.solver:
			choice = self.solver.get_variable_values(f"select({self.player_name},_,s0,M).", 1)
			if choice:
				choice = choice[0]
				self.choices.append(choice)
				logger.debug(f"Agent {self.name} made choice: {choice}")
				return choice

		logger.debug(f"Agent {self.name} is not valid!")
		# TODO runtime error
		return None

	def update(self, opponent_move):
		"""
		Updates the agent's payoff and logs the opponent's choice.

		:param opponent_move: The choice made by the opponent in the current round.
		"""
		if self.solver:
			self.opponent_choices.append(opponent_move)
			payoff = self.solver.get_variable_values(
				f"finally(goal({self.player_name}, U), do(choice({self.player_name}, '{self.choices[-1]}'), do(choice({self.opponent_name}, '{self.opponent_choices[-1]}'), s0))).", 1)
			updated = self.solver.apply_predicate(f"initialise(last_move({self.opponent_name}, '{opponent_move}'), s0).")
			if payoff and updated:
				payoff = float(payoff[0])
				self.payoffs.append(payoff)
				logger.debug(f"Agent {self.name} received payoff: {payoff} and logged opponent's choice: {opponent_move}")
				# TODO update the opponent move in Prolog
				return True
			else:
				return False
		else:
			logger.debug(f"Agent {self.name} is not valid!")
			# TODO runtime error
			return False

	def update_default_move(self, move):
		"""
		Updates default move in the Prolog solver.

		:return: Status of the update.
		"""
		if move not in self.game.possible_moves:
			raise ValueError("The move is not in the set of possible moves!")
		else:
			success = self.solver.apply_predicate(f"initialise(default_move(_, '{move}'), s0).")
			return success

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
