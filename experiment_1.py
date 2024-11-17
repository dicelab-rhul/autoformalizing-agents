import configparser
from src.tournament import Tournament
from src.utils import read_file, log_tournament
import logging
import os
import pandas as pd

'''
In this experiment, a dataset of 55 natural-language game-theoretic scenarios is autoformalized into formal logic 
specifications. To ensure syntactic correctness, a Prolog solver is employed for validation. For semantic validation, 
a tournament is conducted in which each agent using a tit-for-tat strategy competes against its clone using 
an anti-tit-for-tat strategy. 
'''


def main():
	logging.debug('Experiment 1')
	config = configparser.ConfigParser()

	# Step 1: Read configuration
	config.read(os.path.normpath("DATA/CONFIG/experiment_1.ini"))

	# Step 2: Extract configuration parameters
	GAME_DIR = os.path.normpath(config.get("Paths", "GAME_DIR"))
	OUT_DIR = config.get("Paths", "OUT_DIR")
	if not os.path.exists(OUT_DIR):
		os.makedirs(OUT_DIR)
	solver_path = os.path.normpath(config.get("Paths", "SOLVER_PATH"))
	template_path = os.path.normpath(config.get("Paths", "TEMPLATE_PATH"))
	feedback_template_path = os.path.normpath(config.get("Paths", "FEEDBACK_TEMPLATE_PATH"))
	num_agents = config.getint("Params", "num_agents")
	num_rounds = config.getint("Params", "num_rounds")
	max_attempts = config.getint("Params", "max_attempts")

	# Step 3: Load game descriptions
	games_payoffs = pd.read_csv("DATA/MISC/payoff_sums_adjusted.csv")

	# Step 4: Run the tournament for each game description
	experiment_name = "experiment_1"
	for idx, row in games_payoffs.iterrows():
		game_desc_file = row["Game File"]
		game_desc = read_file(os.path.join(GAME_DIR, game_desc_file))
		target_payoffs = [row["Row Player Payoff Sum"]]*num_agents
		# Create and play tournament
		tournament = Tournament(game_desc, target_payoffs=target_payoffs, num_agents=num_agents,
								max_attempts=max_attempts, num_rounds=num_rounds, solver_path=solver_path,
								prompt_path=template_path, feedback_prompt_path=feedback_template_path,
								use_default_strategy=True, clones=True)
		tournament.create_agents()
		tournament.play_tournament()
		winners = tournament.get_winners()

		exp_dir = os.path.join("LOGS", experiment_name)
		log_tournament(experiment_dir=exp_dir, tournament=tournament, tournament_name=game_desc_file[:-4])
		# Print winners
		print("Winners are:")
		for winner in winners:
			print(f"Agent {winner.name} with strategy {winner.strategy_name} and payoff {winner.get_total_payoff()}")


if __name__ == "__main__":
	main()
