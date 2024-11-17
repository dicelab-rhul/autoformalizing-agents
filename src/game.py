from typing import List, Optional


class Game:
	"""
	Represents a game with a natural language description, Prolog rules, possible moves, and player names.
	"""

	def __init__(self, game_string: str, game_rules: Optional[str] = None, game_moves: Optional[List[str]] = None):
		"""
		Initializes the Game object.

		Args:
			game_string (str): A natural language description of the game.
			game_rules (Optional[str]): A Prolog program describing the rules of the game.
			game_moves (Optional[List[str]]): A list of possible moves.
		"""
		self.game_string: str = game_string
		self.game_rules: Optional[str] = game_rules
		self.possible_moves: List[str] = game_moves if game_moves else []
		self.player_names: List[str] = []

	def set_possible_moves(self, moves: List[str]) -> None:
		"""
		Set the possible moves for the game.

		Args:
			moves (List[str]): A list of valid moves.
		"""
		if not isinstance(moves, list) or not all(isinstance(move, str) for move in moves):
			raise ValueError("Moves should be a list of strings.")
		self.possible_moves = moves

	def get_possible_moves(self) -> List[str]:
		"""
		Get the list of possible moves for the game.

		Returns:
			List[str]: A list of possible moves.
		"""
		return self.possible_moves

	def add_possible_move(self, move: str) -> None:
		"""
		Add a single move to the list of possible moves.

		Args:
			move (str): A move to be added.
		"""
		if move not in self.possible_moves:
			self.possible_moves.append(move)

	def set_players(self, players: List[str]) -> None:
		"""
		Set the list of players for the game.

		Args:
			players (List[str]): A list of player names.
		"""
		if not isinstance(players, list) or not all(isinstance(player, str) for player in players):
			raise ValueError("Players should be a list of strings.")
		self.player_names = players

	def get_players(self) -> List[str]:
		"""
		Get the list of players for the game.

		Returns:
			List[str]: A list of player names.
		"""
		return self.player_names

	def add_player(self, player: str) -> None:
		"""
		Add a single player to the list of players.

		Args:
			player (str): A player name to be added.
		"""
		if player not in self.player_names:
			self.player_names.append(player)

	def set_rules(self, rules: str) -> None:
		"""
		Set the rules for the game.

		Args:
			rules (str): A Prolog program describing the rules of the game.
		"""
		if not isinstance(rules, str):
			raise ValueError("Game rules should be a string.")
		self.game_rules = rules

	def get_rules(self) -> Optional[str]:
		"""
		Get the rules of the game.

		Returns:
			Optional[str]: A string with the game rules, or None if not set.
		"""
		return self.game_rules

	def clear_rules(self) -> None:
		"""
		Clear the game rules.
		"""
		self.game_rules = None

	def __repr__(self) -> str:
		"""
		Return a string representation of the Game object.

		Returns:
			str: A string representation of the Game.
		"""
		return (f"Game(description={self.game_string[:30]}..., "
				f"rules={'set' if self.game_rules else 'not set'}, "
				f"moves={len(self.possible_moves)}, players={len(self.player_names)})")
