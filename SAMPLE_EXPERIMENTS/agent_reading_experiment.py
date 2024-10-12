import configparser
from src.tournament import Tournament
from src.utils import read_file, log_tournament
import logging
import os


def main():
	logging.debug('Test')

	# Read experiment parameters
	config = configparser.ConfigParser()
	config.read(os.path.normpath("../DATA/CONFIG/config.ini"))

	GAME_DIR = os.path.normpath(config.get("Paths", "GAME_DIR"))
	OUT_DIR = config.get("Paths", "OUT_DIR")
	if not os.path.exists(OUT_DIR):
		os.makedirs(OUT_DIR)
	solver_path = os.path.normpath(config.get("Paths", "SOLVER_PATH"))

	num_agents = config.getint("Params", "num_agents")
	num_rounds = config.getint("Params", "num_rounds")
	target_payoffs = config.get("Params", "target_payoffs")
	target_payoffs = [int(x) for x in target_payoffs.split(';')]

	# Read sample game description
	game_descriptions = [read_file(os.path.join(GAME_DIR, "pd_noncanonic_test.txt"))]

	experiment_name = "dummy_experiment"

	for game_desc in game_descriptions:
		# Create and play tournament
		tournament = Tournament(game_desc, target_payoffs=target_payoffs, num_agents=num_agents,
								num_rounds=num_rounds, solver_path=solver_path, clones=True, jsons_path=os.path.join(
				"../DATA", "AGENTS"), root="..")
		tournament.create_agents()
		tournament.play_tournament()
		winners = tournament.get_winners()

		# log the state of each agent at the end of the tournament:
		exp_dir = os.path.join("../LOGS", experiment_name)
		log_tournament(experiment_dir=exp_dir, tournament=tournament)
		# Print winners
		print("Winners are:")
		for winner in winners:
			print(f"Agent {winner.name} with strategy {winner.strategy_name} and payoff {winner.get_total_payoff()}")


if __name__ == "__main__":
	main()
