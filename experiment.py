import configparser
from src.tournament import Tournament
from src.utils import read_file
import logging
import os

import json
from datetime import datetime


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
		exp_dir = os.path.join("LOGS",experiment_name)
		log_tournament(experiment_dir=exp_dir, tournament=tournament)
		# Print winners
		print("Winners are:")
		for winner in winners:
			print(f"Agent {winner.name} with strategy {winner.strategy_name} and payoff {winner.get_total_payoff()}")


def log_tournament(experiment_dir, tournament):
	timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
	tournament_dir = os.path.join(experiment_dir, f"tournament_{timestamp}")
	os.makedirs(tournament_dir, exist_ok=True)

	# Log tournament info
	tournament_info = {
		"game_description": tournament.game_description,
		"num_agents": tournament.num_agents,
		"num_rounds": tournament.num_rounds,
		"target_payoffs": tournament.target_payoffs,
		"winners_payoffs": [(winner.name, winner.strategy_name, winner.get_total_payoff()) for winner in tournament.get_winners()]
	}
	with open(os.path.join(tournament_dir, "tournament_info.json"), "w") as f:
		json.dump(tournament_info, f, indent=2, default=set_default)

	# Log each agent's info
	for agent in tournament.agents:
		game = agent.game
		agent_log = {
			"name": agent.name,
			"strategy_name": agent.strategy_name,
			"strategy": agent.strategy,
			"game_rules": game.game_rules,
			"game_moves": game.possible_moves,
			"status": agent.status, #TODO: handle other cases
			"moves": agent.moves,
			"payoffs": agent.payoffs,
			"total_payoff": agent.get_total_payoff()
		}
		with open(os.path.join(tournament_dir, f"agent_{agent.name}.json"), "w") as f:
			json.dump(agent_log, f, indent=2, default=set_default)
		
def set_default(obj):
    if isinstance(obj, set):
        return list(obj)
    raise TypeError

if __name__ == "__main__":
	main()
