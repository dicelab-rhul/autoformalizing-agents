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
	It also keeps track of its payoffs, moves, and opponent's moves.
	"""

	def __init__(self, game_string=None, strategy_path="DATA/STRATEGIES/tit-for-tat.pl", solver_path="src/solver.pl",
				 prompt_path="DATA/PROMPTS/prompt_template.txt", game_path=None, strategy_string=None):
		"""
		Initializes the Agent with a random name, an empty payoff list, moves list, and opponent's moves list.
		"""
		self.name = generate_agent_name(3)
		self.payoffs = []  # List to store the agent's payoffs over time
		self.moves = []  # List to store the agent's moves
		self.opponent_moves = []  # List to store the opponent's moves

		self.game = Game(game_string)  # Game information object
		if strategy_path:
			self.strategy_name = strategy_path.split(os.sep)[-1][:-3]
			self.strategy = read_file(strategy_path)  #game.game
			self.strategy_formalise = False
		else:
			self.strategy_name = self.name+"_strategy"
			self.strategy = strategy_string
			self.strategy_formalise = True

		self.default_move = None
		self.player_name = None
		self.opponent_name = None

		self.solver_path = solver_path  # Path to domain-independent solver
		self.prompt_path = prompt_path  # Path to prompt template

		self.solver = None  # Solver object
		self.llm = GPT4()

		self.valid = self.init(game_path)

	def init(self, game_rules_path=None):
		"""
		Initializes the agent with the game.

		:return: syntactic correctness
		"""
		logger.debug(f"Agent {self.name} with strategy {self.strategy_name} is initializing.")

		# Autoformalisation mode
		if game_rules_path is None:
			game_rules = self.autoformalise(self.prompt_path, "game_description", self.game.game_string)
			if game_rules:
				self.game.set_rules(game_rules)
			else:
				return False
		# Read mode
		else:
			game_rules = read_file(os.path.normpath(game_rules_path))
			self.game.set_rules(game_rules)

		if self.strategy_formalise:
			strategy_rules = self.autoformalise(self.prompt_path, "strategy_description", self.strategy) # TODO strategy prompt
			if strategy_rules:
				self.strategy = strategy_rules
			else:
				return False

		return self.load_solver()

	# TODO set default move method

	def load_solver(self):
		solver_string = read_file(self.solver_path)

		if self.game and solver_string:
			self.solver = Solver(solver_string, self.game.game_rules, self.strategy)

			if self.solver:
				default_move = self.solver.get_variable_values("initially(default_move(_, X), s0).", 1) # TODO default move for the player
				possible_moves = self.solver.get_variable_values("possible(move(_,X), s0).")
				player_names = self.solver.get_variable_values("holds(player(N), s0).")

				if default_move and possible_moves and player_names:
					self.game.set_possible_moves(set(possible_moves))
					self.default_move = default_move[0]
					self.player_name = player_names[0]
					self.opponent_name = player_names[1]
					self.game.set_players(player_names)
					logger.debug(f"Agent {self.name} has possible moves {self.game.get_possible_moves()} and default"
								 f" move {self.default_move}. The player name is {self.player_name} "
								 f"and the opponent name is {self.opponent_name}.")
				else:
					return False
			# TODO if not valid syntactic error
			return self.solver.valid
		return False

	def update_strategy(self, strategy_path):
		self.strategy = strategy_path
		self.load_solver()

	def autoformalise(self, prompt_path, to_replace, replace_string):
		prompt = read_file(prompt_path)
		prompt = prompt.replace('{'+to_replace+'}', replace_string)
		response = self.llm.prompt(prompt)
		try:
			rules = parse_axioms(response)
			return rules
		except ValueError:
			# TODO instruction following error ('@' not added)
			logger.debug(f"Agent {self.name} experienced instruction following error!")
			return None

	def play(self):
		"""
		The agent making a move in the tournament.
		"""
		if self.solver:
			move = self.solver.get_variable_values(f"select({self.player_name},_,s0,M).", 1)
			if move:
				move = move[0]
				self.moves.append(move)
				logger.debug(f"Agent {self.name} made move: {move}")
				return move

		logger.debug(f"Agent {self.name} is not valid!")
		# TODO runtime error
		return None

	def update(self, opponent_move):
		"""
		Updates the agent's payoff and logs the opponent's move.

		:param opponent_move: The move made by the opponent in the current round.
		"""
		if self.solver:
			self.opponent_moves.append(opponent_move)
			payoff = self.solver.get_variable_values(
				f"finally(goal({self.player_name}, U), do(move({self.player_name}, '{self.moves[-1]}'), do(move({self.opponent_name}, '{self.opponent_moves[-1]}'), s0))).", 1)
			updated = self.solver.apply_predicate(f"initialise(last_move({self.opponent_name}, '{opponent_move}'), s0).")
			if payoff and updated:
				payoff = float(payoff[0])
				self.payoffs.append(payoff)
				logger.debug(f"Agent {self.name} received payoff: {payoff} and logged opponent's move: {opponent_move}")
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
