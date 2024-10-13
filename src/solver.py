from src.setup_logger import logger
from swiplserver import PrologMQI
import io
import logging
import tempfile
import os


class Solver:
	"""
	Solver class for managing interactions with a solver.
	"""

	def __init__(self, solver_string: str, game_string: str, strategy: str):
		"""
		Initialize the Solver with the path to the Prolog solver.

		Args:
			solver_string (str): Domain-independent solver.
			game_string (str): Domain-dependent solver.
			strategy (str): Strategy.
		"""
		# Create prolog thread to query the solver
		self.valid = False
		self.prolog_thread = PrologMQI().create_thread()
		self.trace = None
		self.full_solver = None
		self.consult_and_validate(solver_string, game_string, strategy)

	def consult_and_validate(self, solver_string: str, game_string: str, strategy: str, predicates=("select/4", "initialise/2", "opposite_move/2")):
		"""
		Consult domain-dependent and domain-independent solvers, and determine syntactic correctness.

		Args:
			solver_string (str): Domain-independent solver path.
			game_string (str): Domain-dependent solver path.
			strategy (str): Strategy.
			predicates (tuple): Tuple of predicates that need to be contained in the solver.
		"""
		log_capture_string = io.StringIO()
		ch = logging.StreamHandler(log_capture_string)
		ch.setLevel(logging.CRITICAL)  # Capture only CRITICAL log messages
		logging.getLogger('swiplserver').addHandler(ch)

		self.full_solver = solver_string + game_string + strategy
		correct = True
		# List of Prolog data to be written to files
		prolog_data = [("solver", solver_string), ("game", game_string), ("strategy", strategy)]
		temp_files = []

		# Ensure the directory exists
		temp_dir = os.path.join(os.getcwd(), "DATA", "TEMP")
		os.makedirs(temp_dir, exist_ok=True)

		try:
			# Write the Prolog data to temporary files
			for _, data in prolog_data:
				with tempfile.NamedTemporaryFile(delete=False, dir=temp_dir, suffix=".pl") as temp_file:
					temp_file.write(data.encode())  # Write data to file
					temp_files.append(temp_file.name)  # Store the file path
			
			# Load each Prolog file in the Prolog solver
			for temp_file_path, data in zip(temp_files, prolog_data):
				temp_file_path = temp_file_path.replace(os.sep, '/')
				result = self.prolog_thread.query(f'consult(\"{temp_file_path}\").')
				logger.debug(f"Prolog file {data[0]} consulted: {result}")
				if os.path.exists(temp_file_path):
					os.remove(temp_file_path)

			for predicate in predicates:
				check_predicate_query = f"current_predicate({predicate})."
				result = self.prolog_thread.query(check_predicate_query)

				if not result:
					correct = False
					logger.debug(f"The predicate {predicate} does not exist.")
					break

		except Exception as e:
			correct = False
			self.trace = str(e)
			logger.error(f"Prolog error trace: {self.trace}")

		log_contents = log_capture_string.getvalue()
		if log_contents and correct:  # If there's a log message, and we haven't caught an exception
			correct = False
			self.trace = log_contents.strip()
			logger.error(f"Prolog error from logs: {self.trace}")

		# Remove the custom log handler
		logging.getLogger('swiplserver').removeHandler(ch)

		self.valid = correct

	def get_variable_values(self, predicate: str, count=None) -> list:
		"""
		Takes a string representing a predicate and returns the value from the solver.

		Args:
			predicate (str): The predicate to evaluate.
			count (int): Number of values to return. None corresponds to full list.

		Returns:
			The evaluated value of the variable.

		Raises:
			ValueError: If the predicate evaluation fails.
		"""
		try:
			final_result = []
			logger.debug("query:" + predicate)
			self.prolog_thread.query_async(predicate, find_all=False)

			while True:
				result = self.prolog_thread.query_async_result()
				if result is None:
					break
				elif result is False:
					logger.debug("result:" + str(result) + "\n")
					return False
				else:
					logger.debug("result:" + str(result) + "\n")
					final_result.append(result)
			if len(final_result) == 0:
				return None
			else:
				values = [list(result[0].values())[0] for result in final_result]
				return values[:count or len(values)]
		except ValueError as e:
			logger.debug(f"Error: {e}")
			return None

	def apply_predicate(self, predicate: str):
		"""
		Takes a string representing a predicate, evaluates it to update the solver's internal state,
		but does not return any value.

		Args:
			predicate (str): The predicate to evaluate and apply to the solver.

		Raises:
			ValueError: If the predicate evaluation or execution fails.
		"""
		try:
			result = self.prolog_thread.query(predicate)
			logger.debug(f"Applied {predicate}: " + str(result))
			return result
		except Exception as e:
			raise ValueError(f"Failed to apply the predicate: {e}")