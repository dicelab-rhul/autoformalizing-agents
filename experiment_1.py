import configparser
from src.tournament import Tournament
from src.utils import read_file, log_tournament
import logging
import os

'''
In this experiment, a dataset of 110 natural-language game-theoretic scenarios is autoformalised into formal logic
specifications. To validate a syntactic correctness, a Prolog solver is used. To validate semantics correctness,
a tournament is played, where each agent plays with strategy tit-for-tat its clone with strategy anti-tit-for-tat. 
'''


def main():
	logging.debug('Experiment 1')

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

	experiment_name = "dummy_experiment"

	for game_desc in game_descriptions:
		# Create and play tournament
		tournament = Tournament(game_desc, target_payoffs=target_payoffs, num_agents=num_agents,
								max_attempts=max_attempts, num_rounds=num_rounds,
								solver_path=solver_path, prompt_path=template_path, clones=True)
		tournament.create_agents()
		tournament.play_tournament()
		winners = tournament.get_winners()

		# log the state of each agent at the end of the tournament:
		# - game-dependent axioms (self.game)
		# - status (correct, syntactic error, semantic error, runtime error, disqualified, instruction following error)
		# we assume that only the winners are semantically correct (they achieved target payoff)
		# - payoffs list
		exp_dir = os.path.join("LOGS", experiment_name)
		log_tournament(experiment_dir=exp_dir, tournament=tournament)
		# Print winners
		print("Winners are:")
		for winner in winners:
			print(f"Agent {winner.name} with strategy {winner.strategy_name} and payoff {winner.get_total_payoff()}")


if __name__ == "__main__":
	main()