from src.game import Game
from src.utils import generate_agent_name
from src.solver import Solver
from src.setup_logger import logger
from src.utils import read_file, parse_axioms, process_trace, process_trace_messages
from llms.gpt4 import GPT4
import os
import json


class Agent:
	"""
	Represents an Agent in the tournament.

	Each agent autoformalises a game description, plays in the tournament, and updates its state.
	It also keeps track of its payoffs, moves, and opponent's moves.
	"""

	def __init__(self, game_string=None, strategy_path="DATA/STRATEGIES/tit-for-tat.pl", solver_path="src/solver.pl",
				 prompt_path="DATA/PROMPTS/prompt_template.txt", feedback_prompt_path="DATA/PROMPTS/feedback_prompt_template.txt",
				 game_path=None, strategy_string=None, strategy_prompt_path=None, max_attempts=1, agent_json=None):
		"""
		Initializes the Agent with a random name, an empty payoff list, moves list, and opponent's moves list.
		"""
		self.name = generate_agent_name(3)
		self.payoffs = []  # List to store the agent's payoffs over time
		self.moves = []  # List to store the agent's moves
		self.opponent_moves = []  # List to store the opponent's moves

		self.game = Game(game_string)  # Game information object
		self.initialized = False

		self.solver_path = solver_path  # Path to domain-independent solver
		self.max_attempts = max_attempts
		self.attempts = 0
		self.trace_messages = []

		if agent_json:
			self.load_agent_from_json(agent_json)
			self.initialized = True

		else:
			if strategy_path:
				self.strategy_name = strategy_path.split(os.sep)[-1][:-3]
				self.strategy = read_file(strategy_path)
				self.strategy_formalise = False
			else:
				self.strategy_name = self.name + "_strategy"
				self.strategy = strategy_string
				self.strategy_formalise = True
		self.strategy_prompt_path = strategy_prompt_path

		self.prompt_path = prompt_path  # Path to prompt template
		self.feedback_prompt_path = feedback_prompt_path

		self.llm = GPT4(save_history=True)

		if not self.initialized:
			self.default_move = None
			self.player_name = None
			self.opponent_name = None
			self.solver = None  # Solver object
			self.valid = self.init(game_path)
			self.status = "correct" if self.valid else "syntactic_error"  #TODO: get an enum for this?
			self.initialized = True

	def load_agent_from_json(self, path_to_json):
		"""
		Loads all agent parameters from a json file.

		:param path_to_json: path to json file
		"""
		with open(path_to_json, 'r') as file:
			data = json.load(file)

		# self.name = data['name']
		self.strategy_name = data['strategy_name']
		self.strategy = data['strategy']
		self.game.set_rules(data['game_rules'])
		self.valid = self.load_solver()
		self.status = "correct" if self.valid else "syntactic_error"
		self.trace_messages = data['trace_messages']

	# in case we were load a saved state without consulting the solver:
	# self.game.possible_moves = data['game_moves']
	# self.game.player_names = data['game_players']
	# self.status = "correct"

	def init(self, game_rules_path=None):
		"""
		Initializes the agent with the game.

		:return: syntactic correctness
		"""
		logger.debug(f"Agent {self.name} with strategy {self.strategy_name} is initializing.")

		self.attempts = 0
		solver_correct = False
		trace = None
		while self.attempts < self.max_attempts and not solver_correct:
			self.attempts += 1

			# Autoformalisation mode
			if game_rules_path is None:
				# First attempt or no solver was created
				logger.debug(f"Agent {self.name} is autoformalising rules.")
				if self.solver is None:
					game_rules = self.autoformalise(self.prompt_path, ["game_description"], [self.game.game_string])
					if game_rules:
						self.game.set_rules(game_rules)
					else:
						continue
				# Subsequent attempt and an error is in the game rules
				elif trace:
					messages = process_trace(trace, self.game.game_rules)
					lines_to_correct = process_trace_messages(messages, self.game.game_rules)
					if lines_to_correct != "":
						logger.debug(f"Agent {self.name} is correcting rules.")
						logger.debug(f"Messages:\n {lines_to_correct}")
						self.trace_messages += lines_to_correct
						game_rules = self.autoformalise(self.feedback_prompt_path, ["code", "messages"], [self.game.game_rules, lines_to_correct])
						if game_rules:
							self.game.set_rules(game_rules)
						else:
							continue

			# Read mode
			else:
				game_rules = read_file(os.path.normpath(game_rules_path))
				self.game.set_rules(game_rules)

			if self.strategy_formalise:
				# First attempt or no solver was created
				if self.solver is None:
					logger.debug(f"Agent {self.name} is autoformalising strategy.")
					strategy_rules = self.autoformalise(self.strategy_prompt_path, ["strategy_description"], [self.strategy])
					if strategy_rules:
						self.strategy = strategy_rules
					else:
						continue
				# Subsequent attempt and an error is in the strategy
				elif trace:
					messages = process_trace(trace, self.strategy)
					lines_to_correct = process_trace_messages(messages, self.strategy)
					if lines_to_correct != "":
						logger.debug(f"Agent {self.name} is correcting strategy.")
						logger.debug(f"Messages:\n {lines_to_correct}")
						self.trace_messages += lines_to_correct
						strategy_rules = self.autoformalise(self.feedback_prompt_path, ["code", "messages"],
														[self.strategy, lines_to_correct])
						if strategy_rules:
							self.strategy = strategy_rules
						else:
							continue
			solver_correct, trace = self.load_solver()

		return solver_correct

	def load_solver(self):
		solver_string = read_file(self.solver_path)

		if self.game and solver_string:
			self.solver = Solver(solver_string, self.game.game_rules, self.strategy)
			if self.solver:
				if self.solver.trace:
					# if not valid syntactic error
					return self.solver.valid, self.solver.trace
				possible_moves = self.solver.get_variable_values("possible(move(_,X), s0).")
				player_names = self.solver.get_variable_values("holds(player(N), s0).")

				if possible_moves and player_names:
					self.player_name = player_names[0]
					self.opponent_name = player_names[1]
					self.game.set_players(player_names)
					self.game.set_possible_moves(set(possible_moves))
					default_move = self.solver.get_variable_values(
						f"initially(default_move({self.player_name}, X), s0).",
						1)
					if default_move:
						self.default_move = default_move[0]
						logger.debug(
							f"Agent {self.name} has possible moves {self.game.get_possible_moves()} and default"
							f" move {self.default_move}. The player name is {self.player_name} "
							f"and the opponent name is {self.opponent_name}.")
					else:
						return False, self.solver.trace
				else:
					return False, self.solver.trace
			# if not valid syntactic error
			return self.solver.valid, self.solver.trace
		return False, None

	def update_strategy(self, strategy_path):
		self.strategy = strategy_path
		self.load_solver()

	def autoformalise(self, prompt_path, placeholders, replace_strings):
		prompt = read_file(prompt_path)
		for placeholder, replace_string in zip(placeholders, replace_strings):
			prompt = prompt.replace('{' + placeholder + '}', replace_string)
		response = self.llm.prompt(prompt)
		try:
			rules = parse_axioms(response)
			return rules
		except ValueError:
			# instruction following error ('@' not added)
			logger.debug(f"Agent {self.name} experienced instruction following error!")
			self.status = 'instruction_following_error'
			return None

	def play(self):
		"""
		The agent making a move in the tournament.
		"""
		if self.solver:
			logger.debug(f"Agent {self.name} with strategy {self.strategy_name} is making a move.")
			move = self.solver.get_variable_values(f"select({self.player_name},_,s0,M).", 1)
			if move:
				move = move[0]
				self.moves.append(move)
				logger.debug(f"Agent {self.name} with strategy {self.strategy_name} made move: {move}")
				return move

		logger.debug(f"Agent {self.name} didn't select move!")
		self.status = 'runtime_error'
		# runtime error
		return None

	def update_payoff(self, opponent_move):
		"""
		Updates the agent's payoff and logs the opponent's move.

		:param opponent_move: The move made by the opponent in the current round.
		"""
		if self.solver:
			self.opponent_moves.append(opponent_move)
			payoff = self.solver.get_variable_values(
				f"finally(goal({self.player_name}, U), do(move({self.player_name}, '{self.moves[-1]}'), do(move({self.opponent_name}, '{self.opponent_moves[-1]}'), s0))).",
				1)
			updated = self.solver.apply_predicate(
				f"initialise(last_move({self.opponent_name}, '{opponent_move}'), s0).")
			if payoff and updated:
				payoff = float(payoff[0])
				self.payoffs.append(payoff)
				logger.debug(f"Agent {self.name} received payoff: {payoff} and logged opponent's move: {opponent_move}")
				# TODO update the opponent move in Prolog
				return True
			else:
				return False
		else:
			logger.debug(f"Agent {self.name} didn't receive payoff!")
			self.status = 'runtime_error'
			# runtime error
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
