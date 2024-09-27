from src.tournament import Tournament
import logging


def main():
	logging.debug('Test')
	tournament = Tournament("", target_payoffs=[9] * 2, num_agents=2, num_rounds=3)
	tournament.create_agents()
	tournament.play_tournament()
	winners = tournament.get_winners()
	print("Winners are:")
	for winner in winners:
		print(f"Agent {winner.name} with strategy {winner.strategy} payoff {winner.get_total_payoff()}")


if __name__ == "__main__":
	main()
