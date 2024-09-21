from src.setup_logger import logger
from swiplserver import PrologMQI
import io
import logging


class Solver:
	"""
	Solver class for managing interactions with a solver.
	"""

	def __init__(self, solver_path):
		"""
		Initialize the Solver with the path to the Prolog solver.

		Args:
			solver_path (str): Solver path.
		"""
		# Store the path to the Prolog solver
		self.solver = solver_path

	def validate(self, game_axioms_file) -> tuple:
		"""
		Execute queries using the provided game axioms path

		Args:
			game_axioms_file: path to the file with an LLM's output

		Returns:
			tuple: bool saying if program correct, error trace.
		"""
		log_capture_string = io.StringIO()
		ch = logging.StreamHandler(log_capture_string)
		ch.setLevel(logging.CRITICAL)  # Capture only CRITICAL log messages
		logging.getLogger('swiplserver').addHandler(ch)

		correct = True
		trace = ""
		with PrologMQI() as mqi:
			with mqi.create_thread() as prolog_thread:
				try:
					# Load the Prolog solver
					result = prolog_thread.query("consult(\"" + self.solver + "\").")
					logger.debug("Solver loaded: " + str(result))

					# Load game specification created by LLM
					query = f"consult(\"OUTPUT/axioms/{game_axioms_file}\")."
					result = prolog_thread.query(query)
					logger.debug("Solver loaded: " + str(result))
					logger.debug(" " + str(result) + "\n")
				except Exception as e:
					correct = False
					trace = str(e)
					logger.error(f"Prolog error trace: {trace}")

		log_contents = log_capture_string.getvalue()
		if log_contents and correct:  # If there's a log message, and we haven't caught an exception
			correct = False
			trace = log_contents.strip()
			logger.error(f"Prolog error from logs: {trace}")

		# Remove the custom log handler
		logging.getLogger('swiplserver').removeHandler(ch)

		return correct, trace
