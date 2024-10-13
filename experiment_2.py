import configparser
from src.tournament import Tournament
from src.utils import read_file, log_tournament
import logging
import os

'''
"Axelrod's tournament". In this experiment, 5 agents with autoformalised rules, one for each of 5 different games,
are loaded. Then, copies of each agent play against each other, using different predefined strategies. The results 
of this tournament show which strategy is on average the most effective for each game. 
'''


def main():
	logging.debug('Experiment 2')

	# Read experiment parameters
	config = configparser.ConfigParser()
	config.read(os.path.normpath("DATA/CONFIG/experiment_2.ini"))

	OUT_DIR = config.get("Paths", "OUT_DIR")
	if not os.path.exists(OUT_DIR):
		os.makedirs(OUT_DIR)
	solver_path = os.path.normpath(config.get("Paths", "SOLVER_PATH"))
	feedback_template_path = os.path.normpath(config.get("Paths", "FEEDBACK_TEMPLATE_PATH"))
	strategies_path = os.path.normpath(config.get("Paths", "STRATEGIES_PATH"))
	agents_path = os.path.normpath(config.get("Paths", "AGENTS_PATH"))

	num_rounds = config.getint("Params", "num_rounds")

	# Read agents and strategies
	strategies = [os.path.join(strategies_path, strat_name) for strat_name in os.listdir(strategies_path)]
	agents = [os.path.join(agents_path, agent) for agent in os.listdir(agents_path)]
	num_agents = len(strategies)

	experiment_name = "experiment_2"

	for agent in agents:
		tournament = Tournament(num_agents=num_agents, num_rounds=num_rounds, solver_path=solver_path,
								strategies_rules_path=strategies_path, feedback_prompt_path=feedback_template_path,
								jsons_path=agent, clones=False)
		tournament.create_agents()
		tournament.play_tournament()
		winners = tournament.get_winners()

		exp_dir = os.path.join("LOGS", experiment_name)
		agent_name = agent.split(os.sep)[-1][:-5]
		log_tournament(experiment_dir=exp_dir, tournament=tournament, tournament_name=agent_name)
		# Print winners
		print("Winners are:")
		for winner in winners:
			print(f"Agent {winner.name} with strategy {winner.strategy_name} and payoff {winner.get_total_payoff()}")


if __name__ == "__main__":
	main()
