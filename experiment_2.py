import configparser
from src.tournament import Tournament
from src.utils import read_file, log_tournament
import logging
import os

'''
In the experiment modeled after "Axelrod's tournament," five agents, each autoformalized with rules for a distinct game,
are loaded. Copies of these agents then compete against each other using various predefined strategies. The tournament 
results show which strategy proves most effective on average for each game.
'''


def main():
	logging.debug('Experiment 2')
	config = configparser.ConfigParser()

	# Step 1: Read configuration
	config.read(os.path.normpath("DATA/CONFIG/experiment_2.ini"))

	# Step 2: Extract configuration parameters
	OUT_DIR = config.get("Paths", "OUT_DIR")
	if not os.path.exists(OUT_DIR):
		os.makedirs(OUT_DIR)
	solver_path = os.path.normpath(config.get("Paths", "SOLVER_PATH"))
	strategies_path = os.path.normpath(config.get("Paths", "STRATEGIES_PATH"))
	agents_path = os.path.normpath(config.get("Paths", "AGENTS_PATH"))
	num_rounds = config.getint("Params", "num_rounds")

	# Step 3: Read agents and strategies
	strategies = [os.path.join(strategies_path, strat_name) for strat_name in os.listdir(strategies_path)]
	agents = [os.path.join(agents_path, agent) for agent in os.listdir(agents_path)]
	num_agents = len(strategies)

	# Step 4: Run the tournament for each agent (game definition)
	experiment_name = "experiment_2"
	for agent in agents:
		tournament = Tournament(num_agents=num_agents, num_rounds=num_rounds, solver_path=solver_path,
								strategies_rules_path=strategies_path, jsons_path=agent, clones=False)
		tournament.create_agents()
		tournament.play_tournament()
		winners = tournament.get_winners()

		exp_dir = os.path.join("LOGS", experiment_name)
		agent_name = agent
		log_tournament(experiment_dir=exp_dir, tournament=tournament, tournament_name=agent_name)
		# Print winners
		print("Winners are:")
		for winner in winners:
			print(f"Agent {winner.name} with strategy {winner.strategy_name} and payoff {winner.get_total_payoff()}")


if __name__ == "__main__":
	main()
