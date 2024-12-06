from src.setup_logger import logger
from swiplserver import PrologMQI
import io
import logging
import tempfile
from typing import List, Optional, Tuple, Union
import os


class Solver:
	"""
	Solver class for managing interactions with a Prolog solver.
	This class handles loading game rules, strategies, and validating the logic using a Prolog solver.
	"""

	def __init__(self, solver_string: str, game_string: str, strategy: str):
		"""
		Initialize the Solver with the necessary Prolog components.

		Args:
			solver_string (str): The domain-independent Prolog solver code.
			game_string (str): The domain-dependent game rules.
			strategy (str): The strategy to be used by the solver.
		"""
		self.valid: bool = False
		self.trace: Optional[str] = None
		self.full_solver: Optional[str] = None

		# Step 1: Initialize the Prolog thread
		self.prolog_thread = self._initialize_prolog_thread()

		# Step 2: Load and validate the solver, game rules, and strategy
		if self.prolog_thread:
			self.consult_and_validate(solver_string, game_string, strategy)

	def _initialize_prolog_thread(self) -> Optional[object]:
		"""
		Initialize a Prolog thread for querying the solver.

		Returns:
			Optional[object]: The Prolog thread object if created successfully, otherwise None.
		"""
		try:
			return PrologMQI().create_thread()
		except Exception as e:
			logger.error(f"Failed to initialize Prolog thread: {e}")
			return None

	def consult_and_validate(
			self,
			solver_string: str,
			game_string: str,
			strategy: str,
			predicates: Tuple[str, ...] = ("select/4", "initialise/2", "opposite_move/2", "finally/2", "possible/2")
	) -> None:
		"""
		Consult domain-dependent and domain-independent Prolog solvers and validate their correctness.

		Args:
			solver_string (str): Domain-independent solver code.
			game_string (str): Domain-dependent game rules.
			strategy (str): Strategy code.
			predicates (Tuple[str]): A tuple of required predicates to validate.

		Sets:
			self.valid (bool): Whether the solver is valid.
			self.trace (Optional[str]): The error trace if validation fails.
		"""
		# Step 1: Capture critical logs from the Prolog server
		log_capture_string, log_handler = self._setup_logging()

		# Step 2: Combine solver components into a full solver program
		self.full_solver = solver_string + game_string + strategy
		correct = True

		# Step 3: Write Prolog components to temporary files and consult them
		temp_files = self._write_prolog_files([
			("solver", solver_string),
			("game", game_string),
			("strategy", strategy)
		])

		try:
			# Step 4: Load and consult Prolog files in the Prolog solver
			for temp_file_path, (label, _) in zip(temp_files, [("solver", solver_string), ("game", game_string),
															   ("strategy", strategy)]):
				if not self.consult_prolog_file(temp_file_path):
					logger.error(f"Failed to consult {label} from file {temp_file_path}")
					correct = False
					break

			# Step 5: Validate required predicates
			if correct and not self._validate_predicates(predicates):
				correct = False

		except Exception as e:
			correct = False
			self.trace = str(e)
			logger.error(f"Prolog error: {self.trace}")

		# Step 6: Check logs for additional error messages
		if correct:
			self._check_logs_for_errors(log_capture_string)

		# Clean up temporary files and logging handlers
		self._cleanup_temp_files(temp_files)
		self._cleanup_logging(log_handler)

		self.valid = correct

	def _setup_logging(self) -> Tuple[io.StringIO, logging.StreamHandler]:
		"""
		Setup logging to capture critical errors from the Prolog server.

		Returns:
			Tuple[io.StringIO, logging.StreamHandler]: The log capture string and handler.
		"""
		log_capture_string = io.StringIO()
		log_handler = logging.StreamHandler(log_capture_string)
		log_handler.setLevel(logging.CRITICAL)
		logging.getLogger('swiplserver').addHandler(log_handler)
		return log_capture_string, log_handler

	def _write_prolog_files(self, prolog_data: List[Tuple[str, str]]) -> List[str]:
		"""
		Write Prolog data to temporary files.

		Args:
			prolog_data (List[Tuple[str, str]]): List of tuples containing labels and data to write.

		Returns:
			List[str]: List of paths to the temporary files created.
		"""
		temp_files = []
		temp_dir = os.path.join(os.getcwd(), "DATA", "TEMP")
		os.makedirs(temp_dir, exist_ok=True)

		for _, data in prolog_data:
			with tempfile.NamedTemporaryFile(delete=False, dir=temp_dir, suffix=".pl") as temp_file:
				temp_file.write(data.encode())
				temp_files.append(temp_file.name)
		return temp_files

	def consult_prolog_file(self, file_path: str) -> bool:
		"""
		Consult a Prolog file in the solver.

		Args:
			file_path (str): Path to the Prolog file.

		Returns:
			bool: True if the file was successfully consulted, False otherwise.
		"""
		try:
			file_path = file_path.replace(os.sep, '/')
			result = self.prolog_thread.query(f'consult("{file_path}").')
			logger.debug(f"Consulted file {file_path}: {result}")
			return bool(result)
		except Exception as e:
			logger.error(f"Error consulting file {file_path}: {e}")
			return False

	def _validate_predicates(self, predicates: Tuple[str, ...]) -> bool:
		"""
		Validate that all required predicates are defined in the solver.

		Args:
			predicates (Tuple[str, ...]): A tuple of predicates to check.

		Returns:
			bool: True if all predicates are found, False otherwise.
		"""
		for predicate in predicates:
			result = self.prolog_thread.query(f"current_predicate({predicate}).")
			if not result:
				logger.debug(f"Missing predicate: {predicate}")
				return False
		return True

	def _check_logs_for_errors(self, log_capture_string: io.StringIO) -> None:
		"""
		Check captured logs for any critical errors.

		Args:
			log_capture_string (io.StringIO): The log capture object.
		"""
		log_contents = log_capture_string.getvalue()
		if log_contents:
			self.valid = False
			self.trace = log_contents.strip()
			logger.error(f"Prolog error from logs: {self.trace}")

	def _cleanup_temp_files(self, temp_files: List[str]) -> None:
		"""
		Delete temporary files created during validation.

		Args:
			temp_files (List[str]): List of file paths to delete.
		"""
		for file_path in temp_files:
			if os.path.exists(file_path):
				os.remove(file_path)

	def _cleanup_logging(self, log_handler: logging.StreamHandler) -> None:
		"""
		Clean up logging by removing the custom log handler.

		Args:
			log_handler (logging.StreamHandler): The log handler to remove.
		"""
		logging.getLogger('swiplserver').removeHandler(log_handler)

	def get_variable_values(self, predicate: str, count: Optional[int] = None) -> Optional[List[Union[str, bool]]]:
		"""
		Retrieves values from the solver based on a given predicate.

		Args:
			predicate (str): The Prolog predicate to evaluate.
			count (Optional[int]): The number of values to return. If None, returns all values.

		Returns:
			Optional[List[Union[str, bool]]]: A list of evaluated variable values, or None if no values are found.

		Raises:
			ValueError: If the predicate evaluation fails.
		"""
		try:
			logger.debug(f"Querying predicate: {predicate}")
			# Step 1: Execute the query asynchronously
			self.prolog_thread.query_async(predicate, find_all=False)

			# Step 2: Retrieve results from the Prolog thread
			final_result = self._collect_query_results()

			# Step 3: Extract and return values from the results
			return self._extract_values(final_result, count)

		except Exception as e:
			logger.error(f"Error querying predicate '{predicate}': {e}")
			return None

	def _collect_query_results(self) -> List[dict]:
		"""
		Collects results from the asynchronous Prolog query.

		Returns:
			List[dict]: A list of query results.
		"""
		final_result = []
		while True:
			result = self.prolog_thread.query_async_result()
			if result is None:
				break
			elif result is False:
				logger.debug("Query returned False.")
				return []
			else:
				logger.debug(f"Result: {result}")
				final_result.append(result)
		return final_result

	def _extract_values(self, results: List[dict], count: Optional[int]) -> Optional[List[Union[str, bool]]]:
		"""
		Extracts variable values from the query results.

		Args:
			results (List[dict]): The list of query results.
			count (Optional[int]): The number of values to return.

		Returns:
			Optional[List[Union[str, bool]]]: A list of extracted values, or None if no values are found.
		"""
		if not results:
			return None

		# Extract the first value from each result dictionary
		values = [list(result[0].values())[0] for result in results if result]
		logger.debug(f"Extracted values: {values}")

		return values[:count] if count is not None else values

	def apply_predicate(self, predicate: str) -> Optional[bool]:
		"""
		Applies a given Prolog predicate to update the solver's internal state.

		Args:
			predicate (str): The Prolog predicate to evaluate and apply.

		Returns:
			Optional[bool]: True if the predicate was successfully applied, False if it failed.
							Returns None if an exception occurs.

		Raises:
			ValueError: If the predicate evaluation or execution fails.
		"""
		try:
			logger.debug(f"Applying predicate: {predicate}")

			# Step 1: Execute the predicate in the Prolog thread
			result = self._execute_predicate(predicate)

			# Step 2: Log and return the result
			if result:
				logger.debug(f"Predicate '{predicate}' applied successfully: {result}")
				return True
			else:
				logger.debug(f"Predicate '{predicate}' failed.")
				return False

		except Exception as e:
			logger.error(f"Failed to apply predicate '{predicate}': {e}")
			return None

	def _execute_predicate(self, predicate: str) -> Optional[bool]:
		"""
		Executes a Prolog query for a given predicate.

		Args:
			predicate (str): The Prolog predicate to execute.

		Returns:
			Optional[bool]: The result of the query, or None if an error occurs.
		"""
		try:
			return self.prolog_thread.query(predicate)
		except Exception as e:
			logger.error(f"Error executing predicate '{predicate}': {e}")
			return None
