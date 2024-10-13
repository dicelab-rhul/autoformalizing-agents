import os
import random
import re
import json
from datetime import datetime


def generate_syllable():
	"""
	Generates a random syllable consisting of a consonant followed by a vowel.

	:return: A string representing a syllable.
	"""
	consonants = "bcdfghjklmnpqrstvwxyz"
	vowels = "aeiou"

	# Pick a random consonant and vowel
	consonant = random.choice(consonants)
	vowel = random.choice(vowels)

	return consonant + vowel


def generate_agent_name(num_syllables=2):
	"""
	Generates an agent name by combining a specified number of syllables.

	:param num_syllables: The number of syllables to use in the name (default is 2).
	:return: A string representing the generated agent name.
	"""
	name = ''.join(generate_syllable() for _ in range(num_syllables))
	return name.capitalize()  # Capitalize the first letter of the name


def parse_axioms(response):
	"""
	Parses game axioms from the given response and saves them to a .pl file.

	Args:
		response (str): The response containing the game axioms to be parsed.

	Returns:
		str: String containing the game axioms.
	"""
	pattern = r'(?m)^@([^@]+)@'
	match = re.search(pattern, response)
	if match is None:
		raise ValueError(f"No match found for pattern: {pattern}")
	game_axioms = match.group(1)

	return game_axioms


def read_file(filename):
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


def set_normalized_path(path):
	"""Normalizes the given path if it's a string, otherwise returns it as is."""
	return os.path.normpath(str(path)) if isinstance(path, str) else path


def log_tournament(experiment_dir, tournament, tournament_name="tournament"):
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
			"trace_messages": agent.trace_messages
		}
		with open(os.path.join(tournament_dir, f"agent_{agent.name}.json"), "w") as f:
			json.dump(agent_log, f, indent=2, default=set_default)


def set_default(obj):
	if isinstance(obj, set):
		return list(obj)
	raise TypeError


def parse_trace(log):
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


def process_trace(trace, full_solver):
	messages = parse_trace(trace)
	solver_lines = full_solver.split('\n')
	for message in messages:
		line = solver_lines[int(message['line'])-1]
		message['line_content'] = line
	return messages


def process_trace_messages(messages, solver):
	lines_to_correct = ""
	for message in messages:
		line_content = message['line_content']
		if line_content in solver:
			lines_to_correct += f"Line: {line_content} produced {message['type']}: {message['message']}\n"
	return lines_to_correct
