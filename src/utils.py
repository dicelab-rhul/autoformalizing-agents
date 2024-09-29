import os
import random
import re


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
