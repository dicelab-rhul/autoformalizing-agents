from src.agent import Agent
from src.setup_logger import logger


class RandomAgent(Agent):
	def play(self):
		"""
		The agent making a move in the tournament.
		"""
		if self.solver:
			possible_moves = ",".join(self.game.possible_moves)
			move = self.solver.get_variable_values(f"select(_,_,[{possible_moves}],M).", 1)
			if move:
				move = move[0]
				self.moves.append(move)
				logger.debug(f"Agent {self.name} with strategy {self.strategy_name} made move: {move}")
				return move

		logger.debug(f"Agent {self.name} didn't select move!")
		self.status = 'runtime_error'
		# runtime error
		return None
