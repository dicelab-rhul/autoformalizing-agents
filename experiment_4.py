import configparser
from src.tournament import Tournament
from src.utils import read_file, log_tournament
import logging
import os

'''
In this experiment, we autoformalise Shannon's mind reading machine. 
'''


def main():
	logging.debug('Experiment 4')

	#TODO

	# Read experiment parameters
	config = configparser.ConfigParser()
	config.read(os.path.normpath("DATA/CONFIG/experiment_4.ini"))

	OUT_DIR = config.get("Paths", "OUT_DIR")
	if not os.path.exists(OUT_DIR):
		os.makedirs(OUT_DIR)
	solver_path = os.path.normpath(config.get("Paths", "SOLVER_PATH"))
	strategies_path = os.path.normpath(config.get("Paths", "STRATEGIES_PATH"))
	game_desc = read_file(os.path.normpath(config.get("Paths", "GAMES_PATH")))
	prompt_path = os.path.normpath(config.get("Paths", "PROMPT_PATH"))
	feedback_template_path = os.path.normpath(config.get("Paths", "FEEDBACK_TEMPLATE_PATH"))

	num_rounds = config.getint("Params", "num_rounds")

	# Read agents and strategies
	strategies = [os.path.join(strategies_path, strat_name) for strat_name in os.listdir(strategies_path)]
	num_agents = len(strategies)

	experiment_name = "experiment_4"

	tournament = Tournament(game_description=game_desc, num_agents=num_agents, num_rounds=num_rounds,
							solver_path=solver_path, prompt_path=prompt_path, feedback_prompt_path=feedback_template_path,
							strategies_path=strategies_path, clones=True)
	tournament.create_agents()
	tournament.play_tournament()
	winners = tournament.get_winners()

	exp_dir = os.path.join("LOGS", experiment_name)
	agent_name = "mind_reading_agent"
	log_tournament(experiment_dir=exp_dir, tournament=tournament, tournament_name=agent_name)
	# Print winners
	print("Winners are:")
	for winner in winners:
		print(f"Agent {winner.name} with strategy {winner.strategy_name} and payoff {winner.get_total_payoff()}")


if __name__ == "__main__":
	main()
