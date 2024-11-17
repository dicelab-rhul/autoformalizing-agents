import os
import json
from typing import List, Optional, Tuple
from llms.gpt4 import GPT4
from src.game import Game
from src.utils import generate_agent_name
from src.solver import Solver
from src.setup_logger import logger
from src.utils import read_file, parse_axioms, process_trace, process_trace_messages


class Agent:
	"""
	Represents an Agent in the tournament.

	Each agent autoformalizes a game description, plays in the tournament, and updates its state.
	It also keeps track of its payoffs, moves, and opponent's moves.
	"""

	def __init__(self,
				 game_string: Optional[str] = None,
				 strategy_path: str = "DATA/STRATEGIES/tit-for-tat.pl",
				 solver_path: str = "src/solver.pl",
				 prompt_path: str = "DATA/PROMPTS/prompt_template.txt",
				 feedback_prompt_path: str = "DATA/PROMPTS/feedback_prompt_template.txt",
				 game_path: Optional[str] = None,
				 strategy_string: Optional[str] = None,
				 strategy_prompt_path: Optional[str] = None,
				 max_attempts: int = 1,
				 agent_json: Optional[str] = None):
		"""
		Initializes the Agent with a name, strategy, game, and other configurations.
		"""
		self.name = generate_agent_name(3)
		self.payoffs = []  # List to store the agent's payoffs over time
		self.moves = []  # List to store the agent's moves
		self.opponent_moves = []  # List to store the opponent's moves
		self.game = Game(game_string)  # Game information object
		self.initialized = False

		# Paths and settings
		self.solver_path = solver_path  # Path to domain-independent solver
		self.max_attempts = max_attempts
		self.attempts = 0
		self.prompt_path = prompt_path  # Path to prompt template
		self.feedback_prompt_path = feedback_prompt_path
		self.strategy_prompt_path = strategy_prompt_path
		self.llm = GPT4(save_history=True)
		self.trace_messages = []

		# Agent strategy
		self.strategy = ""
		self.strategy_name = "unnamed_strategy"
		self.strategy_formalize = False

		if agent_json:
			self.load_agent_from_json(agent_json)
			self.initialized = True

		else:
			if strategy_path:
				self.strategy_name = strategy_path.split(os.sep)[-1].replace(".pl", "")
				self.strategy = read_file(strategy_path)
				self.strategy_formalize = False
		if strategy_string:
			self.strategy_name = self.name + "_strategy"
			self.strategy = strategy_string
			self.strategy_formalize = True

		if not self.initialized:
			self.default_move = None
			self.player_name = None
			self.opponent_name = None
			self.solver = None  # Solver object
			self.valid = self.init(game_path)

		if agent_json and self.strategy_formalize:
			self.strategy = strategy_string
			self.solver = None
			self.valid = self.init(game_rules_string=self.game.game_rules)

		self.status = "correct" if self.valid else "syntactic_error"
		self.initialized = True

	def load_agent_from_json(self, path_to_json: str) -> None:
		"""
		Load all agent parameters from a JSON file.

		Args:
			path_to_json (str): Path to the JSON file.
		"""
		with open(path_to_json, 'r') as file:
			data = json.load(file)
		self.strategy_name = data['strategy_name']
		self.strategy = data['strategy']
		self.game.set_rules(data['game_rules'])
		self.trace_messages = data.get('trace_messages', [])
		self.valid = self.load_solver()
		self.status = "correct" if self.valid else "syntactic_error"

	def init(self, game_rules_path: Optional[str] = None, game_rules_string: Optional[str] = None) -> bool:
		"""
		Initialize the agent with game rules and strategy.

		Args:
			game_rules_path (Optional[str]): Path to game rules file.
			game_rules_string (Optional[str]): Game rules as a string.

		Returns:
			bool: True if the initialization is successful, False otherwise.
		"""
		logger.debug(f"Agent {self.name} with strategy {self.strategy_name} is initializing.")

		self.attempts = 0
		solver_correct = False
		trace = None

		while self.attempts < self.max_attempts and not solver_correct:
			self.attempts += 1

			if game_rules_string:
				self.game.set_rules(game_rules_string)
			# Autoformalization mode
			elif game_rules_path is None:
				# First attempt or no solver was created
				logger.debug(f"Agent {self.name} is autoformalizing rules.")
				if self.solver is None:
					game_rules = self.autoformalize(self.prompt_path, ["game_description"], [self.game.game_string])
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
						self.trace_messages.append(lines_to_correct)
						game_rules = self.autoformalize(self.feedback_prompt_path, ["code", "messages"],
														[self.game.game_rules, lines_to_correct])
						if game_rules:
							self.game.set_rules(game_rules)
						else:
							continue

			# Read from file mode
			else:
				game_rules = read_file(os.path.normpath(game_rules_path))
				self.game.set_rules(game_rules)

			if self.strategy_formalize:
				# First attempt or no solver was created
				if self.solver is None:
					logger.debug(f"Agent {self.name} is autoformalizing strategy.")
					strategy_rules = self.autoformalize(self.strategy_prompt_path, ["strategy_description"],
														[self.strategy])
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
						self.trace_messages.append(lines_to_correct)
						strategy_rules = self.autoformalize(self.feedback_prompt_path, ["code", "messages"],
															[self.strategy, lines_to_correct])
						if strategy_rules:
							self.strategy = strategy_rules
						else:
							continue
			solver_correct, trace = self.load_solver()

		return solver_correct

	def load_solver(self) -> Tuple[bool, Optional[str]]:
		"""
		Load the solver for the agent using the game rules and strategy.

		Returns:
			Tuple[bool, Optional[str]]: A tuple where the first element indicates if the solver is valid,
										and the second element is the trace message if any issues occur.
		"""
		# Step 1: Read the solver string from the file
		solver_string = read_file(self.solver_path)
		if not solver_string or not self.game:
			return False, None

		# Step 2: Initialize the solver with the game rules and strategy
		self.solver = Solver(solver_string, self.game.game_rules, self.strategy)

		# Step 3: Validate the solver and process the trace if it exists
		if not self.solver or self.solver.trace:
			return self.solver.valid, self.solver.trace if self.solver else (False, None)

		# Step 4: Extract game variables (moves and player names)
		if not self._extract_game_variables():
			return False, self.solver.trace

		# Step 5: Extract the default move if available
		if not self._extract_default_move():
			return False, self.solver.trace

		logger.debug(
			f"Agent {self.name} has possible moves {self.game.get_possible_moves()} and default move {self.default_move}. "
			f"The player name is {self.player_name} and the opponent name is {self.opponent_name}."
		)

		return True, None

	def _extract_game_variables(self) -> bool:
		"""
		Extract the possible moves and player names from the solver.

		Returns:
			bool: True if both possible moves and player names are successfully extracted, False otherwise.
		"""
		possible_moves = self.solver.get_variable_values("possible(move(_,X), s0).")
		player_names = self.solver.get_variable_values("holds(player(N), s0).")

		if possible_moves and player_names:
			self.player_name = player_names[0]
			self.opponent_name = player_names[1]
			self.game.set_players(player_names)
			self.game.set_possible_moves(list(set(possible_moves)))
			return True

		return False

	def _extract_default_move(self) -> bool:
		"""
		Extract the default move for the agent from the solver.

		Returns:
			bool: True if a default move is successfully extracted, False otherwise.
		"""
		default_move = self.solver.get_variable_values(
			f"initially(default_move({self.player_name}, X), s0).", 1
		)
		if default_move:
			self.default_move = default_move[0]
			return True
		return False

	def update_strategy(self, strategy_path: str) -> None:
		"""
		Update the agent's strategy using a new strategy file path.

		Args:
			strategy_path (str): The file path to the new strategy.
		"""
		self.strategy = strategy_path
		self.load_solver()

	def autoformalize(self, prompt_path: str, placeholders: List[str], replace_strings: List[str]) -> Optional[str]:
		"""
		Autoformalize rules or strategies using a prompt template.

		This method uses a language model (LLM) to generate formal rules based on a natural language description.

		Args:
			prompt_path (str): Path to the prompt template.
			placeholders (List[str]): List of placeholders in the template to be replaced.
			replace_strings (List[str]): List of strings to replace the placeholders.

		Returns:
			Optional[str]: The formalized rules if successful, or None if an error occurs.
		"""
		# Step 1: Prepare the prompt by replacing placeholders
		prompt = self._prepare_prompt(prompt_path, placeholders, replace_strings)

		# Step 2: Get the response from the LLM
		response = self.llm.prompt(prompt)

		# Step 3: Parse the response to extract formalized game/strategy rules
		return self._parse_response(response)

	def _prepare_prompt(self, prompt_path: str, placeholders: List[str], replace_strings: List[str]) -> str:
		"""
		Prepare the prompt by reading a template file and replacing placeholders.

		Args:
			prompt_path (str): Path to the prompt template.
			placeholders (List[str]): List of placeholders to replace.
			replace_strings (List[str]): List of strings to replace the placeholders.

		Returns:
			str: The prepared prompt with placeholders replaced.
		"""
		prompt = read_file(prompt_path)
		for placeholder, replace_string in zip(placeholders, replace_strings):
			prompt = prompt.replace(f'{{{placeholder}}}', replace_string)
		return prompt

	def _parse_response(self, response: str) -> Optional[str]:
		"""
		Parse the response from the LLM to extract formalized rules.

		Args:
			response (str): The response text from the LLM.

		Returns:
			Optional[str]: The extracted rules, or None if parsing fails.
		"""
		try:
			rules = parse_axioms(response)
			return rules
		except ValueError:
			# Log error if response parsing fails
			logger.debug(f"Agent {self.name} experienced an instruction-following error!")
			self.status = 'instruction_following_error'
			return None

	def play(self) -> Optional[str]:
		"""
		The agent makes a move in the tournament.

		Uses the solver to determine the next move based on the current game state.
		If a move is successfully selected, it is stored in the agent's move history.

		Returns:
			Optional[str]: The move selected by the agent, or None if no valid move is made.
		"""
		if not self.solver:
			logger.debug(f"Agent {self.name} is unable to play due to an uninitialized solver.")
			self.status = 'runtime_error'
			return None

		logger.debug(f"Agent {self.name} with strategy {self.strategy_name} is making a move.")

		# Step 1: Attempt to get a move using the solver
		move = self._select_move()
		if move:
			self.moves.append(move)
			logger.debug(f"Agent {self.name} with strategy {self.strategy_name} made move: {move}")
			return move

		# If no move is selected, log the error and update status
		logger.debug(f"Agent {self.name} did not select a move!")
		self.status = 'runtime_error'
		return None

	def _select_move(self) -> Optional[str]:
		"""
		Use the solver to select the agent's move.

		Returns:
			Optional[str]: The move selected by the solver, or None if no move is found.
		"""
		if not self.solver or not self.player_name:
			return None

		move = self.solver.get_variable_values(f"select({self.player_name}, _, s0, M).", 1)
		return move[0] if move else None

	def update_payoff(self, opponent_move: str) -> bool:
		"""
		Update the agent's payoff based on the opponent's move.

		Logs the opponent's move, calculates the agent's payoff using the solver, and updates the agent's state.

		Args:
			opponent_move (str): The move made by the opponent in the current round.

		Returns:
			bool: True if the payoff was successfully updated, False otherwise.
		"""
		if not self.solver:
			logger.debug(f"Agent {self.name} cannot update payoff due to an uninitialized solver.")
			self.status = 'runtime_error'
			return False

		# Step 1: Log the opponent's move
		self.opponent_moves.append(opponent_move)

		# Step 2: Calculate payoff using the solver
		payoff = self._calculate_payoff()
		if not payoff:
			return False

		# Step 3: Update the solver state with the opponent's last move
		if not self._update_solver_state(opponent_move):
			return False

		# Step 4: Log the successful update and store the payoff
		self.payoffs.append(payoff)
		logger.debug(f"Agent {self.name} received payoff: {payoff} and logged opponent's move: {opponent_move}")
		return True

	def _calculate_payoff(self) -> Optional[float]:
		"""
		Calculate the agent's payoff based on the last move using the solver.

		Returns:
			Optional[float]: The calculated payoff if successful, otherwise None.
		"""
		if not self.moves or not self.opponent_moves:
			return None

		query = (
			f"finally(goal({self.player_name}, U), "
			f"do(move({self.player_name}, '{self.moves[-1]}'), "
			f"do(move({self.opponent_name}, '{self.opponent_moves[-1]}'), s0)))."
		)
		payoff = self.solver.get_variable_values(query, 1)
		return float(payoff[0]) if payoff else None

	def _update_solver_state(self, opponent_move: str) -> bool:
		"""
		Update the solver state with the opponent's last move.

		Args:
			opponent_move (str): The move made by the opponent.

		Returns:
			bool: True if the solver state was successfully updated, otherwise False.
		"""
		query = f"initialise(last_move({self.opponent_name}, '{opponent_move}'), s0)."
		return self.solver.apply_predicate(query)

	def update_default_move(self, move: str) -> bool:
		"""
		Update the default move in the Prolog solver.

		Args:
			move (str): The move to set as the default move.

		Returns:
			bool: True if the update was successful, False otherwise.

		Raises:
			ValueError: If the move is not in the set of possible moves.
		"""
		if not self._is_valid_move(move):
			raise ValueError(f"The move '{move}' is not in the set of possible moves!")

		# Apply the default move update in the solver
		return self._apply_default_move_update(move)

	def _is_valid_move(self, move: str) -> bool:
		"""
		Check if the provided move is valid.

		Args:
			move (str): The move to validate.

		Returns:
			bool: True if the move is valid, False otherwise.
		"""
		return move in self.game.get_possible_moves()

	def _apply_default_move_update(self, move: str) -> bool:
		"""
		Apply the default move update in the solver.

		Args:
			move (str): The move to set as default.

		Returns:
			bool: True if the update was successful, False otherwise.
		"""
		query = f"initialise(default_move(_, '{move}'), s0)."
		success = self.solver.apply_predicate(query)
		logger.debug(f"Updated default move to '{move}' with status: {success}")
		return success

	def get_payoffs(self) -> List[float]:
		"""
		Get the list of payoffs accumulated by the agent.

		Returns:
			List[float]: The list of payoffs.
		"""
		return self.payoffs

	def get_total_payoff(self) -> float:
		"""
		Get the total payoff accumulated by the agent.

		Returns:
			float: The total sum of payoffs.
		"""
		total = sum(self.payoffs)
		logger.debug(f"Total payoff for agent {self.name}: {total}")
		return total
