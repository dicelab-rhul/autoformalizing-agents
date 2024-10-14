import configparser
from src.tournament import Tournament
from src.utils import read_file, log_tournament
import logging
import os

'''
In this experiment, we autoformalise strategies, providing a game solver and a tit-for-tat strategy as an example. 
'''


def main():
	logging.debug('Experiment 3')

	# TODO add target payoffs

	# Read experiment parameters
	config = configparser.ConfigParser()
	config.read(os.path.normpath("DATA/CONFIG/experiment_3.ini"))

	OUT_DIR = config.get("Paths", "OUT_DIR")
	if not os.path.exists(OUT_DIR):
		os.makedirs(OUT_DIR)
	solver_path = os.path.normpath(config.get("Paths", "SOLVER_PATH"))
	strategies_path = os.path.normpath(config.get("Paths", "STRATEGIES_PATH"))
	agent_path = os.path.normpath(config.get("Paths", "AGENT_PATH"))
	feedback_template_path = os.path.normpath(config.get("Paths", "FEEDBACK_TEMPLATE_PATH"))
	strategy_template_path = os.path.normpath(config.get("Paths", "STRATEGY_PROMPT"))

	num_rounds = config.getint("Params", "num_rounds")
	num_agents = config.getint("Params", "num_agents")

	experiment_name = "experiment_3"

	tournament = Tournament(num_agents=num_agents, num_rounds=num_rounds, solver_path=solver_path,
							feedback_prompt_path=feedback_template_path, strategy_prompt_path=strategy_template_path,
							strategies_path=strategies_path, jsons_path=agent_path, clones=True)
	tournament.create_agents()
	tournament.play_tournament()
	winners = tournament.get_winners()

	exp_dir = os.path.join("LOGS", experiment_name)
	log_tournament(experiment_dir=exp_dir, tournament=tournament, tournament_name="strategies")
	# Print winners
	print("Winners are:")
	for winner in winners:
		print(f"Agent {winner.name} with strategy {winner.strategy_name} and payoff {winner.get_total_payoff()}")


if __name__ == "__main__":
	main()
