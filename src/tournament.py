from src.agent import Agent
import itertools


class Tournament:
	def __init__(self, game="pd", num_agents=10, max_attempts=5, num_rounds=10, strategies=None, target_payoffs=None):
		"""
		Initialize a Tournament instance.

		Args:
			game (str): The type of game (default is "pd" for Prisoner's Dilemma).
			num_agents (int): The number of agents in the tournament (default is 10).
			max_attempts (int): The maximum number attempts at creating syntactically valid agent
			strategies (list): List of strategies used by the agents (default is None).
			target_payoffs (list): List of target payoffs for the agents (default is None).
		"""
		self.game = game
		self.min_agents = 2
		self.max_agents = 50
		if not (self.min_agents <= num_agents <= self.max_agents):
			raise ValueError(
				f"num_agents must be between {self.min_agents} and {self.max_agents}. You provided {num_agents}.")
		if num_agents % 2 != 0:
			raise ValueError(f"num_agents must be an even number. You provided {num_agents}.")
		self.num_agents = num_agents
		self.max_attempts = max_attempts
		self.num_rounds = num_rounds
		self.strategies = strategies if strategies else []
		self.target_payoffs = target_payoffs if target_payoffs else []
		self.default_strategy = "tit-for-tat"
		self.agents = []

	def create_agents(self):
		"""
		Create agents based on the game and strategies provided.
		"""
		# If strategies are not provided, use default strategy for all agents
		if self.strategies is None:
			self.strategies = [self.default_strategy] * self.num_agents
		# Check if the number of strategies equals the number of agents
		if len(self.strategies) != self.num_agents:
			raise ValueError("The number of strategies provided does not match the number of agents.")

		game = None  #TODO read game
		synt_correct = False
		for strategy in self.strategies:
			for i in range(self.max_attempts):
				agent = Agent(game, strategy)
				synt_correct = agent.init()
				if synt_correct:
					self.agents.append(agent)
					break
			if not synt_correct:
				raise RuntimeError(
					f"Couldn't create requested number of syntactically correct agents in {self.max_attempts} attempts.")

	def play_tournament(self):
		"""
		Simulate the tournament by having agents play the game.
		"""
		if not self.agents:
			raise ValueError("Agents must be created before playing the tournament.")
		agent_pairs = itertools.combinations(self.agents, 2)
		for agent1, agent2 in agent_pairs:
			for round in range(self.num_rounds):
				move_agent_1 = agent1.play()
				move_agent_2 = agent2.play()
				agent1.update(move_agent_2)
				agent2.update(move_agent_1)

	def get_winners(self):
		"""
		Determine the winners of the tournament.
		If the target payoffs are provided, winners are all agents that obtained their target payoff.
		If there are no target payoffs, the winners are all agents with the highest payoff.
		"""
		# Check if expected_utilities is provided and not empty
		if self.target_payoffs:
			# Collect all agents who achieved or exceeded their expected utility
			winners = [agent for (i, agent) in enumerate(self.agents) if agent.get_total_payoff() == self.target_payoffs[i]]
		else:
			# Find the highest payoff among all agents
			max_payoff = max(agent.get_total_payoff() for agent in self.agents)
			# Collect all agents with the highest payoff
			winners = [agent for agent in self.agents if agent.get_total_payoff() == max_payoff]

		return winners
