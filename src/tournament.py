import itertools
import os
import tempfile
from src.agent import Agent
from src.setup_logger import logger
from src.utils import read_file, set_normalized_path


class Tournament:
	def __init__(self, game_description=None, num_agents=10, max_attempts=5, num_rounds=10, clones=True,
				 target_payoffs=None, solver_path="src/solver.pl", prompt_path="DATA/PROMPTS/prompt_template.txt",
				 strategies_path=None, game_rules_path=None, strategies_rules_path=None, strategy_prompt_path=None, jsons_path=None, root="."):
		"""
		Initialize a Tournament instance.

		Args:
			game_description (str): The natural language game description. If None use predefined agents.
			num_agents (int): The number of agents in the tournament (default is 10).
			max_attempts (int): The maximum number attempts at creating syntactically valid agent (default is 5).
			num_rounds (int): The number of tournament rounds.
			clones (bool): Should the agents use the same, default strategy (default is True).
			target_payoffs (list): List of target payoffs for the agents (default is None).
			solver_path (str): Path to the solver.
			prompt_path (str): Path to the prompt template.
			strategies_path (str): Path to strategies used by the agents (default is None).
			game_rules_path (str): Path to formalised game rules.
			strategies_rules_path (str): Path to formalised strategies.
		"""
		self.root = root
		self.game_description = game_description
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
		self.clones = clones
		self.default_strategy = os.path.join(self.root,set_normalized_path("DATA/STRATEGIES/tit-for-tat.pl"))
		self.solver_path = set_normalized_path(solver_path)  # Path to domain-independent solver
		self.prompt_path = set_normalized_path(prompt_path)  # Path to prompt template
		self.game_rules_path = set_normalized_path(game_rules_path)  # Path to domain-dependent solver
		self.strategies_path = set_normalized_path(strategies_path)  # Path to strategy natural language descriptions
		self.strategies_rules_path = set_normalized_path(strategies_rules_path)  # Path to strategy axioms
		self.strategy_prompt_path = strategy_prompt_path  # Path to a prompt for autoformalising strategy
		self.target_payoffs = target_payoffs if target_payoffs else []
		self.strategies = []
		self.jsons_path = jsons_path
		self.agents = []
		self.invalid_agents = []

	def create_agents(self):
		"""
		Create agents based on the game and strategies provided.
		"""
		# If clones mode, use default strategy for all agents
		if self.clones:
			self.strategies = [self.default_strategy] * self.num_agents

		# Read predefined strategies
		elif self.strategies_rules_path:
			for f in os.listdir(self.strategies_rules_path):
				self.strategies.append(read_file(os.path.join(self.strategies_rules_path, f)))

		# Autoformalise strategies
		elif self.strategies_path:
			for f in os.listdir(self.strategies_path):
				self.strategies.append(read_file(os.path.join(self.strategies_path, f)))

		# Check if the number of strategies equals the number of agents
		if len(self.strategies) != self.num_agents:
			raise ValueError("The number of strategies provided does not match the number of agents.")

		if self.jsons_path is not None:
			jsons_list = list(os.listdir(self.jsons_path))
			if len(jsons_list) == 1:  # One agent for a tournament with different strategies
				jsons_list = jsons_list*self.num_agents
			if len(self.strategies) != len(jsons_list):
				raise ValueError("The number of strategies provided does not match the number of saved agents.")

		synt_correct = False
		for strat_num, strategy in enumerate(self.strategies):
			for i in range(self.max_attempts):
				strategy_rules = None
				strategy_string = None

				if self.clones or self.strategies_rules_path:
					strategy_rules = strategy
				else:
					strategy_string = strategy

				agent_json = None
				if self.jsons_path is not None:
					json_path = jsons_list[strat_num]
					agent_json = os.path.join(self.jsons_path, json_path)

				agent = Agent(self.game_description, strategy_rules, self.solver_path, self.prompt_path, self.game_rules_path,
							  strategy_string, self.strategy_prompt_path, agent_json=agent_json)
				if agent.valid:
					self.agents.append(agent)
					synt_correct = True
					break
				else:
					self.invalid_agents.append(agent)
			if not synt_correct:
				raise RuntimeError(
					f"Couldn't create requested number of syntactically correct agents in {self.max_attempts} attempts.")

	def play_tournament(self):
		"""
		The tournament with agents playing the game.
		"""
		if not self.agents:
			raise ValueError("Agents must be created before playing the tournament.")

		if self.clones:
			agent_clones = []
			for agent in self.agents:
				with tempfile.NamedTemporaryFile(mode='w+', dir=os.path.join("DATA", "TEMP"), suffix=".pl", delete=False) as temp_file:
					temp_file.write(agent.game.game_rules)
				clone = Agent(strategy_path=os.path.join(self.root, "DATA", "STRATEGIES", "anti-tit-for-tat.pl"), game_path=temp_file.name, solver_path=self.solver_path)
				clone.name = agent.name+"_clone"
				agent_clones.append(clone)
				os.remove(temp_file.name)
			agent_pairs = [(agent, clone) for (agent, clone) in zip(self.agents, agent_clones)]

		else:
			agent_pairs = itertools.combinations(self.agents, 2)

		for agent1, agent2 in agent_pairs:
			valid_pair = True
			for round_num in range(self.num_rounds):
				logger.debug(f"\nAgent {agent1.name} vs {agent2.name}, Round {round_num}.")
				move_agent_1, move_agent_2 = agent1.play(), agent2.play()
				if not (move_agent_1 and move_agent_2):
					valid_pair = False
				else:
					updated_1, updated_2 = agent1.update_payoff(move_agent_2), agent2.update_payoff(move_agent_1)
					if not (updated_1 and updated_2):
						valid_pair = False
				if not valid_pair:
					logger.debug(
						f"Agent {agent1.name} or {agent2.name} not valid. Excluding the pair from the tournament")
					agent1.state = 'disqualified'
					agent2.state = 'disqualified'
				# disqualified error

	def get_winners(self):
		"""
		Determine the winners of the tournament.
		If the target payoffs are provided, winners are all agents that obtained their target payoff.
		If there are no target payoffs, the winners are all agents with the highest payoff.
		"""
		# Check if expected_utilities is provided and not empty
		if self.target_payoffs:
			# Collect all agents who achieved or exceeded their expected utility
			winners = [agent for (i, agent) in enumerate(self.agents) if
					   agent.get_total_payoff() == self.target_payoffs[i]]
		else:
			# Find the highest payoff among all agents
			max_payoff = max(agent.get_total_payoff() for agent in self.agents)
			# Collect all agents with the highest payoff
			winners = [agent for agent in self.agents if agent.get_total_payoff() == max_payoff]

		return winners
