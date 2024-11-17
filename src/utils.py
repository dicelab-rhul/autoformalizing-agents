import os
import random
import re
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from src.tournament import Tournament

def generate_syllable() -> str:
	"""
	Generates a random syllable using a combination of consonants and vowels.

	Returns:
		str: A randomly generated syllable.
	"""
	consonants = "bcdfghjklmnpqrstvwxyz"
	vowels = "aeiou"

	# Pick a random consonant and vowel
	consonant = random.choice(consonants)
	vowel = random.choice(vowels)

	return consonant + vowel


def generate_agent_name(num_syllables: int = 2) -> str:
	"""
	Generates a random agent name by combining a specified number of syllables.

	The generated name is capitalized, with the first letter in uppercase.

	Args:
		num_syllables (int): The number of syllables to use in the name (default is 2).

	Returns:
		str: A randomly generated agent name.

	Raises:
		ValueError: If the number of syllables is less than 1.
	"""
	name = ''.join(generate_syllable() for _ in range(num_syllables))
	return name.capitalize()  # Capitalize the first letter of the name


def parse_axioms(response: str) -> str:
	"""
	Parses game axioms from the given response and extracts the content enclosed within '@' symbols.

	This function looks for content enclosed between two '@' symbols in the given response.
	If the content is found, it extracts and returns it. If no such content is found, a `ValueError` is raised.

	Args:
		response (str): The response string containing the game axioms to be parsed.

	Returns:
		str: A string containing the extracted game axioms.

	Raises:
		ValueError: If no content matching the pattern is found in the response.
	"""
	pattern = r'(?m)^@([^@]+)@'
	match = re.search(pattern, response)
	if match is None:
		raise ValueError(f"No match found for pattern: {pattern}")
	game_axioms = match.group(1)

	return game_axioms


def read_file(filename: str) -> Optional[str]:
	"""
	Reads the content of a file and returns it as a string.

	Args:
		filename (str): The path to the file to be read.

	Returns:
		Optional[str]: The content of the file as a string if successful, or None if an error occurs.

	Raises:
		FileNotFoundError: If the specified file does not exist.
		IOError: If an error occurs while reading the file.
	"""
	try:
		with open(filename) as f:
			s = f.read()
			return s
	except FileNotFoundError:
		print(f"The file {filename} was not found.")
		return None
	except IOError:
		print("An error occurred while reading the file.")
		return None


def set_normalized_path(path: Union[str, None]) -> Optional[str]:
	"""
	Normalizes the given file path if it's a string. If the input is not a string, returns it unchanged.

	Args:
		path (Union[str, None]): The file path to normalize, or None.

	Returns:
		Optional[str]: The normalized file path if it's a valid string, otherwise None.
	"""
	if isinstance(path, str):
		normalized_path = os.path.normpath(path)
		return normalized_path
	return path


def log_tournament(
	experiment_dir: str,
	tournament: 'Tournament',
	tournament_name: str = "tournament"
) -> None:
	"""
	Logs the details of a tournament, including its configuration and agents' information.

	Args:
		experiment_dir (str): The directory where the tournament logs will be saved.
		tournament (Tournament): The tournament object containing all relevant data.
		tournament_name (str): The name of the tournament (default is "tournament").
	"""
	timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
	tournament_dir = os.path.join(experiment_dir, f"{tournament_name}_{timestamp}")
	os.makedirs(tournament_dir, exist_ok=True)

	# Log tournament info
	tournament_info = {
		"game_description": tournament.game_description,
		"num_agents": tournament.num_agents,
		"num_rounds": tournament.num_rounds,
		"target_payoffs": tournament.target_payoffs,
		"winners_payoffs": [(winner.name, winner.strategy_name, winner.get_total_payoff()) for winner in
							tournament.get_winners()]
	}
	with open(os.path.join(tournament_dir, "tournament_info.json"), "w") as f:
		json.dump(tournament_info, f, indent=2, default=set_default)

	# Log each agent's info
	agents = tournament.agents + tournament.invalid_agents
	for agent in agents:
		game = agent.game
		agent_log = {
			"name": agent.name,
			"strategy_name": agent.strategy_name,
			"strategy": agent.strategy,
			"game_rules": game.game_rules,
			"game_moves": game.possible_moves,
			"game_players": game.player_names,
			"status": agent.status,
			"moves": agent.moves,
			"payoffs": agent.payoffs,
			"total_payoff": agent.get_total_payoff(),
			"default_move": agent.default_move,
			"trace_messages": agent.trace_messages,
			"attempts": agent.attempts
		}
		with open(os.path.join(tournament_dir, f"agent_{agent.name}.json"), "w") as f:
			json.dump(agent_log, f, indent=2, default=set_default)


def set_default(obj: Any) -> Any:
	"""
	Helper function for handling non-serializable objects during JSON serialization.

	This function converts a set to a list for JSON serialization. If the object is not
	a set, it raises a TypeError.

	Args:
		obj (Any): The object to serialize.

	Returns:
		Any: The object converted to a serializable format if possible.

	Raises:
		TypeError: If the object is not serializable (i.e., not a set).
	"""
	if isinstance(obj, set):
		return list(obj)
	raise TypeError


def parse_trace(log: str) -> List[Dict[str, any]]:
	"""
	Parses a log string to extract warning and error messages, along with their line numbers.

	This function uses regular expressions to identify warnings and errors in the log. It then extracts
	the line numbers and messages, formats them, and returns a list of parsed entries.

	Args:
		log (str): The log string containing warnings and errors.

	Returns:
		List[Dict[str, any]]: A list of dictionaries, where each dictionary represents a parsed entry with:
							  - 'type': The type of the entry ('Warning' or 'Error').
							  - 'line': The line number where the issue occurred.
							  - 'message': The extracted warning or error message.
	"""
	parsed_entries = []
	# Define regex patterns for warnings and errors
	warning_pattern = r"Warning: .*:(\d+):\nWarning:\s+(.*)"
	error_pattern = r"ERROR: .*:(\d+):\d+: (.*)"

	# Find all warning matches
	for match in re.finditer(warning_pattern, log):
		line_number = match.group(1)
		message = match.group(2).strip()
		parsed_entries.append({'type': 'Warning', 'line': int(line_number), 'message':  re.sub(r"/[^:]+:", "line ", message)})

	# Find all error matches
	for match in re.finditer(error_pattern, log):
		line_number = match.group(1)
		message = match.group(2).strip()
		parsed_entries.append({'type': 'Error', 'line': int(line_number), 'message': re.sub(r"/[^:]+:", "line ", message)})

	return parsed_entries


def process_trace(trace: str, full_solver: str) -> List[Dict[str, Any]]:
	"""
	Processes a trace log to extract error/warning messages and associates them with their corresponding lines in the solver code.

	Args:
		trace (str): The trace log containing warnings and errors.
		full_solver (str): The full solver code as a string, split by lines.

	Returns:
		List[Dict[str, Any]]: A list of dictionaries where each entry contains:
			- 'type': The type of message ('Warning' or 'Error').
			- 'line': The line number where the issue occurred.
			- 'message': The extracted warning or error message.
			- 'line_content': The actual content of the corresponding line in the solver code.
	"""
	messages = parse_trace(trace)
	solver_lines = full_solver.split('\n')
	for message in messages:
		line = solver_lines[int(message['line'])-1]
		message['line_content'] = line
	return messages


def process_trace_messages(messages: List[Dict[str, str]], solver: str) -> str:
	"""
	Processes trace messages to generate a report of lines that produced warnings or errors.

	This function checks if each message's line content is present in the solver code and, if so,
	formats a report indicating which lines caused warnings or errors.

	Args:
		messages (List[Dict[str, str]]): A list of dictionaries containing trace messages with:
			- 'type': The type of message ('Warning' or 'Error').
			- 'line_content': The content of the line that caused the issue.
			- 'message': The detailed warning or error message.
		solver (str): The full solver code as a single string.

	Returns:
		str: A formatted string listing the lines in the solver code that produced warnings or errors.
	"""
	lines_to_correct = ""
	for message in messages:
		line_content = message['line_content']
		if line_content in solver:
			lines_to_correct += f"Line: {line_content} produced {message['type']}: {message['message']}\n"
	return lines_to_correct
