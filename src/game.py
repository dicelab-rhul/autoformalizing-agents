class Game:

	def __init__(self, game_string, game_rules = None, game_moves = []):
		"""
		Initializes the Game with a natural language description of the game and a Prolog strategy.

		:param game_string: A string of natural language description of the game.
		"""
		self.game_string = game_string  # natural language description
		self.game_rules = game_rules  # autoformalised game rules
		self.possible_moves = game_moves  # Possible moves from autoformalised game rules
		self.player_names = []

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

	def set_players(self, players):
		"""
		Set the list of players for the game.

		:param players: A list of moves.
		:return: None
		"""
		self.player_names = players

	def get_players(self):
		"""
		Return a list of players for the game.

		:return: A list of player names.
		"""
		return self.player_names

	def set_rules(self, rules):
		"""
		Set the rules for the game.

		:param rules: A string with Prolog program describing the rules.
		:return: None
		"""
		self.game_rules = rules

