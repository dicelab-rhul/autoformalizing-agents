import configparser
from src.tournament import Tournament
from src.utils import read_file
import logging
import os


def main():
	logging.debug('Test')

	# Read experiment parameters
	config = configparser.ConfigParser()
	config.read(os.path.normpath("DATA/CONFIG/config.ini"))

	GAME_DIR = os.path.normpath(config.get("Paths", "GAME_DIR"))
	OUT_DIR = config.get("Paths", "OUT_DIR")
	if not os.path.exists(OUT_DIR):
		os.makedirs(OUT_DIR)
	solver_path = os.path.normpath(config.get("Paths", "SOLVER_PATH"))
	template_path = os.path.normpath(config.get("Paths", "TEMPLATE_PATH"))

	num_agents = config.getint("Params", "num_agents")
	num_rounds = config.getint("Params", "num_rounds")
	max_attempts = config.getint("Params", "max_attempts")
	target_payoffs = config.get("Params", "target_payoffs")
	target_payoffs = [int(x) for x in target_payoffs.split(';')]

	# Read sample game description
	game_descriptions = [read_file(os.path.join(GAME_DIR, "pd_noncanonic_test.txt"))]

	for game_desc in game_descriptions:
		# Create and play tournament
		tournament = Tournament(game_desc, target_payoffs=target_payoffs, num_agents=num_agents, max_attempts=max_attempts,
								num_rounds=num_rounds, solver_path=solver_path, prompt_path=template_path)
		tournament.create_agents()
		tournament.play_tournament()
		winners = tournament.get_winners()

		# TODO log the state of each agent at the end of the tournament:
		# - game-dependent axioms (self.game)
		# - status (correct, syntactic error, semantic error, runtime error, disqualified, instruction following error)
		# we assume that only the winners are semantically correct (they achieved target payoff)
		# - payoffs list

		# Print winners
		print("Winners are:")
		for winner in winners:
			print(f"Agent {winner.name} with strategy {winner.strategy} and payoff {winner.get_total_payoff()}")


if __name__ == "__main__":
	main()
