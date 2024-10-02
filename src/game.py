class Game:

	def __init__(self, game_string):
		"""
		Initializes the Game with a natural language description of the game and a Prolog strategy.

		:param game_string: A string of natural language description of the game.
		:param strategy: The strategy to be employed during the game (Prolog).
		"""
		self.game_string = game_string  # natural language description
		self.game_rules = None  # autoformalised game rules
		self.possible_moves = []  # Possible moves from autoformalised game rules

	def set_possible_moves(self, moves):
		"""
		Set the possible moves for the game.

		:param moves: A list of moves.
		:return: None
		"""
		self.possible_moves = moves

	def get_possible_moves(self):
		"""
		Return a list of possible moves for the game.

		:return: A list of strings representing possible moves.
		"""
		return self.possible_moves

	def set_rules(self, rules):
		"""
		Set the rules for the game.

		:param rules: A string with Prolog program describing the rules.
		:return: None
		"""
		self.game_rules = rules


