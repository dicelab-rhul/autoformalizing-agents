import os
import json
import pandas as pd
from src.solver import Solver
from src.utils import read_file
import re


class Validator:
	"""
	A class to validate auto-formalized games.
	"""

	def __init__(self, agents_dir: str, matrices_file: str, payoffs_file: str, validators_dir: str):
		"""
		Initializes the Validator with the given directory and file paths.

		Args:
			agents_dir (str): Path to the directory containing agent files.
			matrices_file (str): Path to the file containing matrix data.
			validators_dir (str): Path to the directory containing validators.
		"""
		self.agents_dir = agents_dir
		with open(matrices_file, 'r') as file:
			matrices = json.load(file)
		self.matrices = matrices
		self.target_payoffs = pd.read_csv(payoffs_file)
		self.validators = self.get_validators(validators_dir)
		self.solver_path = "../src/solver.pl"  # game-independent part of the solver
		self.strategy = "../DATA/STRATEGIES/tit-for-tat.pl"  # strategy
		self.general_agent_file = "../DATA/MISC/general_agent.pl"
		self.solver = None
		self.result_headers = ['filename', 'agent_name', 'status', 'tournament', 'constraints', 'final']
		self.results = []
		self.actions = {'bs': [('F', 'F'), ('O', 'O'), ('O', 'F'), ('F', 'O')],
						'pd': [('C', 'C'), ('D', 'C'), ('C', 'D'), ('D', 'D')],
						'mp': [('H', 'H'), ('T', 'H'), ('T', 'T'), ('H', 'T')],
						'sh': [('S', 'S'), ('S', 'H'), ('H', 'S'), ('H', 'H')],
						'hd': [('S', 'S'), ('D', 'S'), ('S', 'D'), ('D', 'D')]}
		self.action_sequence = {'bs': [('O', 'O'), ('O', 'F'), ('F', 'F'), ('F', 'O')],
								'pd': [('C', 'C'), ('C', 'D'), ('D', 'D'), ('D', 'C')],
								'mp': [('H', 'H'), ('H', 'T'), ('T', 'T'), ('T', 'H')],
								'sh': [('S', 'S'), ('S', 'H'), ('H', 'H'), ('H', 'S')],
								'hd': [('S', 'S'), ('S', 'D'), ('D', 'D'), ('D', 'S')]}

	def get_validators(self, validators_dir):
		validators_list = list(os.listdir(validators_dir))
		validators = {filename.replace(".pl", ""): os.path.join(validators_dir, filename) for filename in
					  validators_list}
		return validators

	def shift_right(self, lst, positions):
		"""
		Shifts the elements of a list to the right by the specified number of positions.
		:param lst: List to shift
		:param positions: Number of positions to shift
		:return: The shifted list
		"""
		# Ensure the shift amount doesn't exceed the list's length
		positions = positions % len(lst)
		# Rearrange the list by slicing
		return lst[-positions:] + lst[:-positions]

	def generate_payoff_array(self, filename, variables=False, shift=0):
		# Extract game type from filename
		game_type_match = re.match(r"^([a-z]+)_", filename)
		if not game_type_match:
			raise ValueError("Invalid filename format. Game type not found.")

		game_type = game_type_match.group(1)

		# Check if game type exists in actions
		if game_type not in self.actions:
			raise ValueError(f"Unknown game type '{game_type}'.")

		# Retrieve actions and matrix
		if variables:
			actions = self.action_sequence[game_type]
			if shift != 0:
				actions = self.shift_right(actions, shift)
			matrix = [('X', '_')] * 4

		else:
			actions = self.actions[game_type]
			if filename not in self.matrices:
				raise ValueError(f"Matrix for filename '{filename}' not found.")

			matrix = self.matrices[filename]

		# Generate payoff strings
		payoff_array = []
		for (action1, action2), (payoff1, payoff2) in zip(actions, matrix):
			if variables:
				payoff_str = f"payoff('{action1}', '{action2}', {payoff1}, {payoff2})."
			else:
				payoff_str = f"assertz(payoff('{action1}', '{action2}', {payoff1}, {payoff2}))."
			payoff_array.append(payoff_str)

		return payoff_array

	def compare_sequences(self, actual, target):
		"""
		Compare whether a lists of payoffs contain the same values in the same order.
		:param actual: List of floats
		:param target: List of integers
		:return: True if they contain the same values in the same order, False otherwise.
		"""
		# Check if both lists have the same length
		if len(actual) != len(target):
			return False

		# Compare element by element after rounding the floats
		for float_value, int_value in zip(actual, target):
			if round(float_value) != int_value:
				return False

		return True

	def compare_payoff_sequence(self, filename, actual_sequence, shift=0):
		payoff_matrix_variables = self.generate_payoff_array(filename, variables=True, shift=shift)
		target_sequence = []
		for predicate in payoff_matrix_variables:
			result = self.solver.get_variable_values(predicate)
			target_sequence += result
		print((actual_sequence, target_sequence))
		same = self.compare_sequences(actual_sequence, target_sequence)
		return same

	def fill_numbers(self, matrix, game_type):
		matrix_joined = []
		for pair in matrix:
			matrix_joined += pair
		matrix_unique = list(set(matrix_joined))
		ms = sorted(matrix_unique, reverse=True)
		if game_type in ['pd', 'sh', 'hd']:
			return f"{game_type}({ms[0]},{ms[1]},{ms[2]},{ms[3]},C,D)."
		if game_type in ['mp']:
			if len(ms) == 4:
				return f"{game_type}({ms[0]},{ms[1]},{ms[2]},{ms[3]},H,T)."
			if len(ms) == 2:
				return f"{game_type}({ms[0]},{ms[0]},{ms[1]},{ms[1]},H,T)."
		if game_type in ['bs']:
			return f"{game_type}({ms[0]},{ms[1]},{ms[2]},F,O)."

	def check_constraints(self, game_type, filename, game_rules):
		validator = self.validators[game_type]
		self.solver = Solver(read_file(self.solver_path), game_rules, read_file(self.strategy))
		self.solver.consult_prolog_file(validator)
		matrix = self.matrices[filename]
		predicate = self.fill_numbers(matrix, game_type)
		values = self.solver.get_variable_values(predicate)
		if values:
			return True
		else:
			return False

	def validate_all(self):
		"""
		Validates auto-formalized code.

		Raises:
			ValueError: If any validation fails.
		"""
		validator_types = list(self.validators.keys())
		for i, agent_dir in enumerate(os.listdir(self.agents_dir)):
			print("Instance", i, agent_dir)
			game_type = agent_dir[:2]

			if game_type in validator_types:
				agent_path = os.listdir(os.path.join(self.agents_dir, agent_dir))
				for agent in agent_path:
					# get filename and name
					filename = '_'.join(agent_dir.split('_')[:3]) + '.txt'
					name = agent[6:-5]
					target_payoff = self.target_payoffs.loc[
						self.target_payoffs['Game File'] == filename, 'Row Player Payoff Sum'].values[0]

					# parse status and rules
					with open(os.path.join(self.agents_dir, agent_dir, agent), 'r') as file:
						if "agent" in agent:  # skip tournament.json
							print("Validating agent ", name)
							result_row = [filename, name]
							data = json.load(file)
							status = data['status']
							result_row += [status]
							if status != 'correct':
								print("Agent ", name, " is ", status)
								result_row += [False, False, False]
								self.results.append(result_row)
								continue

							# validate total payoff
							total_payoff = data['total_payoff']
							if total_payoff != target_payoff:
								print("Agent ", name, " did not achieve target payoff")
								tournament_status = False

							# If the total target payoff is correct, we validate the sequence
							else:
								actual_sequence = data['payoffs']
								self.solver = Solver(read_file(self.solver_path), read_file(self.general_agent_file),
													 read_file(self.strategy))
								payoff_matrix = self.generate_payoff_array(filename)
								# load payoff matrix specific for the game
								for predicate in payoff_matrix:
									self.solver.apply_predicate(predicate)

								same = self.compare_payoff_sequence(filename, actual_sequence)
								if not same: # may still be valid if default move different, we need to shift by two
									same = self.compare_payoff_sequence(filename, actual_sequence,2)
								print("Agent ", name, " achieved target payoff sequence:", same)
								tournament_status = same
							result_row += [tournament_status]

							# validate constraints
							game_rules = data['game_rules']
							constraint_status = self.check_constraints(game_type, filename, game_rules)
							print("Agent ", name, " satisfies constraints")
							result_row += [constraint_status]

							result_row += [tournament_status&constraint_status]
							self.results.append(result_row)

		df = pd.DataFrame(self.results, columns=self.result_headers)
		return df



