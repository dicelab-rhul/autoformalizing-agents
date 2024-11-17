import itertools
import os
import tempfile
from typing import List, Optional, Tuple
from src.agent import Agent
from src.agents.random_agent import RandomAgent
from src.setup_logger import logger
from src.utils import read_file, set_normalized_path


class Tournament:
	"""
	A class representing a game tournament with multiple agents and strategies.

	Attributes:
		root (str): The root directory for paths.
		game_description (Optional[str]): Natural language game description.
		min_agents (int): Minimum number of agents allowed.
		max_agents (int): Maximum number of agents allowed.
		num_agents (int): Number of agents participating in the tournament.
		max_attempts (int): Maximum attempts to create valid agents.
		num_rounds (int): Number of rounds in the tournament.
		clones (bool): Whether agents use the same strategy and play against their clones.
		use_default_strategy (bool): Flag to use the default strategy.
		default_strategy (str): Path to the default strategy file.
		clone_strategy (str): Path to the clones' strategy file.
		solver_path (str): Path to the solver.
		prompt_path (str): Path to the prompt template.
		feedback_prompt_path (str): Path to the feedback prompt template.
		game_rules_path (Optional[str]): Path to the game rules.
		strategies_path (Optional[str]): Path to agent strategies.
		strategies_rules_path (Optional[str]): Path to strategy rules.
		strategy_prompt_path (Optional[str]): Path to strategy prompt.
		jsons_path (Optional[str]): Path to stored JSON files.
		target_payoffs (List[float]): List of target payoffs for agents.
		strategies (List[str]): List of strategies used in the tournament.
		agents (List): List of agents participating in the tournament.
		invalid_agents (List): List of invalid agents created.
	"""

	def __init__(self,
				 game_description: Optional[str] = None,
				 num_agents: int = 10,
				 max_attempts: int = 5,
				 num_rounds: int = 10,
				 clones: bool = True,
				 target_payoffs: Optional[List[float]] = None,
				 solver_path: str = "src/solver.pl",
				 prompt_path: str = "DATA/PROMPTS/prompt_template.txt",
				 feedback_prompt_path: str = "DATA/PROMPTS/feedback_prompt_template.txt",
				 strategies_path: Optional[str] = None,
				 clone_strategy: str = "DATA/STRATEGIES/anti-tit-for-tat.pl",
				 game_rules_path: Optional[str] = None,
				 strategies_rules_path: Optional[str] = None,
				 strategy_prompt_path: Optional[str] = None,
				 jsons_path: Optional[str] = None,
				 use_default_strategy: bool = False,
				 root: str = "."):
		"""
		Initialize a Tournament instance with the specified parameters.

		Args:
			game_description (Optional[str]): The natural language game description. If None, predefined agents are used.
			num_agents (int): Number of agents in the tournament (default is 10).
			max_attempts (int): Maximum number of attempts to create valid agents (default is 5).
			num_rounds (int): Number of rounds in the tournament (default is 10).
			clones (bool): Whether agents use the same strategy and play against their clone (default is True).
			target_payoffs (Optional[List[float]]): List of target payoffs for agents (default is None).
			solver_path (str): Path to the solver (default is "src/solver.pl").
			prompt_path (str): Path to the prompt template (default is "DATA/PROMPTS/prompt_template.txt").
			feedback_prompt_path (str): Path to the feedback prompt template.
			strategies_path (Optional[str]): Path to strategies (default is None).
			clone_strategy (str): Path to the clones' strategy file (default is "DATA/STRATEGIES/anti-tit-for-tat.pl").
			game_rules_path (Optional[str]): Path to game rules (default is None).
			strategies_rules_path (Optional[str]): Path to strategy rules (default is None).
			strategy_prompt_path (Optional[str]): Path to a strategy prompt (default is None).
			jsons_path (Optional[str]): Path to store JSON files (default is None).
			use_default_strategy (bool): Whether to use the default strategy (default is False).
			root (str): Root directory for paths (default is ".").

		Raises:
			ValueError: If num_agents is not within the allowed range.
		"""
		self.root = root
		self.game_description = game_description

		# Validate the number of agents
		self.min_agents = 1
		self.max_agents = 50
		if not (self.min_agents <= num_agents <= self.max_agents):
			raise ValueError(
				f"num_agents must be between {self.min_agents} and {self.max_agents}. You provided {num_agents}.")
		self.num_agents = num_agents

		self.max_attempts = max_attempts
		self.num_rounds = num_rounds
		self.clones = clones
		self.use_default_strategy = use_default_strategy

		# Set up paths
		self.default_strategy = os.path.join(self.root, set_normalized_path("DATA/STRATEGIES/tit-for-tat.pl"))
		self.clone_strategy = os.path.join(self.root, set_normalized_path(clone_strategy))
		self.solver_path = set_normalized_path(solver_path)
		self.prompt_path = set_normalized_path(prompt_path)
		self.feedback_prompt_path = set_normalized_path(feedback_prompt_path)
		self.game_rules_path = set_normalized_path(game_rules_path)
		self.strategies_path = set_normalized_path(strategies_path)
		self.strategies_rules_path = set_normalized_path(strategies_rules_path)
		self.strategy_prompt_path = strategy_prompt_path
		self.jsons_path = jsons_path
		self.jsons_list = None

		# Initialize other attributes
		self.target_payoffs = target_payoffs if target_payoffs else []
		self.strategies = []
		self.agents = []
		self.invalid_agents = []

	def __repr__(self) -> str:
		"""
		Return a string representation of the Tournament object.

		Returns:
			str: String representation of the Tournament.
		"""
		return (f"Tournament(num_agents={self.num_agents}, num_rounds={self.num_rounds}, "
				f"clones={self.clones}, use_default_strategy={self.use_default_strategy})")

	def create_agents(self) -> None:
		"""
		Create agents based on the game description and provided strategies.

		Agents are generated based on one of the following scenarios:
		1. If `use_default_strategy` is True, all agents use the same default strategy.
		2. If `strategies_rules_path` is specified, agents are created using pre-defined strategy rules.
		3. If `strategies_path` is provided, strategies are autoformalized from text files.
		4. If `jsons_path` is specified, agents are loaded from pre-existing JSON files.

		Raises:
			ValueError: If the number of strategies does not match the number of agents.
		"""
		# Step 1: Determine strategies based on the specified configuration
		self._initialize_strategies()

		# Step 2: Validate that the number of strategies matches the number of agents
		self._validate_strategies()

		# Step 3: Create agents based on the strategies and JSON files (if any)
		self._create_agents_from_strategies()

	def _initialize_strategies(self) -> None:
		"""
		Initialize strategies based on the specified configuration.
		"""
		# Case 1: Use the default strategy for all agents if clones mode is enabled
		if self.use_default_strategy:
			self.strategies = [self.default_strategy] * self.num_agents

		# Case 2: Read predefined strategies from strategy rules files
		elif self.strategies_rules_path:
			self.strategies, self.strategies_names = self._load_strategies_from_rules()

		# Case 3: Auto-formalize strategies from text files
		elif self.strategies_path:
			self.strategies, self.strategies_names = self._load_strategies_from_text()
			self._adjust_num_agents_based_on_strategies()

		# Case 4: Use mock strategies if only JSON agents are provided
		elif self.jsons_path:
			self.strategies = [None] * self.num_agents

	def _validate_strategies(self) -> None:
		"""
		Validate that the number of strategies matches the number of agents.
		Raises a ValueError if there is a mismatch.
		"""
		if len(self.strategies) != self.num_agents:
			raise ValueError("The number of strategies provided does not match the number of agents.")

		# If using JSON files, ensure that the number of agents and strategies match
		if self.jsons_path:
			self.jsons_list = os.listdir(self.jsons_path)
			if len(self.jsons_list) == 1:
				self.jsons_list *= self.num_agents
			if len(self.strategies) != len(self.jsons_list):
				raise ValueError("The number of strategies does not match the number of saved agents.")

	def _create_agents_from_strategies(self) -> None:
		"""
		Create agents using the initialized strategies and JSON files (if any).
		"""
		for strat_num, strategy in enumerate(self.strategies):
			strategy_rules = strategy if self.strategies_rules_path or self.use_default_strategy else None
			strategy_string = strategy if self.strategies_path else None

			agent_json = None
			if self.jsons_path:
				self.json_path = self.jsons_list[strat_num]
				agent_json = os.path.join(self.jsons_path, self.json_path)

			agent_class = self._get_agent_class(strat_num)
			agent = agent_class(
				game_string=self.game_description,
				strategy_path=strategy_rules,
				solver_path=self.solver_path,
				prompt_path=self.prompt_path,
				feedback_prompt_path=self.feedback_prompt_path,
				game_path=self.game_rules_path,
				strategy_string=strategy_string,
				strategy_prompt_path=self.strategy_prompt_path,
				max_attempts=self.max_attempts,
				agent_json=agent_json
			)

			# Override strategy if JSON agents are provided with strategy rules
			if self.jsons_path and self.strategies_rules_path:
				agent.strategy = strategy
				agent.strategy_name = self.strategies_names[strat_num]
				agent.load_solver()

			if self.strategies_path:
				agent.strategy_name = self.strategies_names[strat_num]

			# Add agent to the appropriate list based on its validity
			if agent.valid:
				self.agents.append(agent)
			else:
				self.invalid_agents.append(agent)

	def _load_strategies_from_rules(self) -> (List[str], List[str]):
		"""
		Load strategies from predefined strategy rules.

		Returns:
			Tuple[List[str], List[str]]: A list of strategies and their corresponding names.
		"""
		strategies = []
		strategy_names = []
		for file in sorted(os.listdir(self.strategies_rules_path)):
			strategies.append(read_file(os.path.join(self.strategies_rules_path, file)))
			strategy_names.append(file[:-3])  # Remove file extension
		return strategies, strategy_names

	def _load_strategies_from_text(self) -> (List[str], List[str]):
		"""
		Load and autoformalize strategies from text files.

		Returns:
			Tuple[List[str], List[str]]: A list of strategies and their corresponding names.
		"""
		strategies = []
		strategy_names = []
		for file in sorted(os.listdir(self.strategies_path)):
			strategies.append(read_file(os.path.join(self.strategies_path, file)))
			strategy_names.append(file.replace(".txt", ""))
		return strategies, strategy_names

	def _adjust_num_agents_based_on_strategies(self) -> None:
		"""
		Adjust the number of agents based on the number of strategies provided.
		"""
		if len(self.strategies) < self.num_agents:
			self.strategies = [strategy for strategy in self.strategies for _ in range(self.num_agents)]
		elif len(self.strategies) > self.num_agents:
			self.num_agents = len(self.strategies)

	def _get_agent_class(self, strat_num: int):
		"""
		Determine the agent class to use based on the strategy name.

		Args:
			strat_num (int): The index of the current strategy.

		Returns:
			Type[Agent]: The agent class to use (either Agent or RandomAgent).
		"""
		if self.strategies_rules_path:
			strategy_name = self.strategies_names[strat_num]
			if "random" in strategy_name:
				return RandomAgent
		return Agent

	def play_tournament(self) -> None:
		"""
		Run the tournament where agents play against each other.
		Raises a ValueError if agents have not been created.
		"""
		# Step 1: Validate that agents have been created
		if not self.agents:
			raise ValueError("Agents must be created before playing the tournament.")

		# Step 2: Generate agent pairs for the tournament
		agent_pairs = self._generate_agent_pairs()

		# Step 3: Conduct matches between agent pairs
		self._play_matches(agent_pairs)

	def _generate_agent_pairs(self) -> List[Tuple[Agent, Agent]]:
		"""
		Generate pairs of agents to play against each other.

		Returns:
			List[Tuple[Agent, Agent]]: A list of tuples representing agent pairs.
		"""
		if self.clones:
			return self._generate_clone_pairs()
		else:
			# Generate pairs using combinations (agents play against each other)
			return list(itertools.combinations_with_replacement(self.agents, 2))

	def _generate_clone_pairs(self) -> List[Tuple[Agent, Agent]]:
		"""
		Generate pairs of agents with clones for head-to-head matches.

		Returns:
			List[Tuple[Agent, Agent]]: A list of tuples with each agent and its clone.
		"""
		agent_clones = []
		for agent in self.agents:
			with tempfile.NamedTemporaryFile(
					mode='w+', dir=os.path.join("DATA", "TEMP"), suffix=".pl", delete=False
			) as temp_file:
				temp_file.write(agent.game.game_rules)
				temp_file_path = temp_file.name

			# Create a clone with the same game rules
			clone = Agent(strategy_path=self.clone_strategy, game_path=temp_file_path, solver_path=self.solver_path)
			clone.name = f"{agent.name}_clone"
			agent_clones.append(clone)

			# Remove the temporary file after cloning
			os.remove(temp_file_path)

		return [(agent, clone) for agent, clone in zip(self.agents, agent_clones)]

	def _play_matches(self, agent_pairs: List[Tuple[Agent, Agent]]) -> None:
		"""
		Play the specified number of rounds between each pair of agents.

		Args:
			agent_pairs (List[Tuple[Agent, Agent]]): List of tuples representing pairs of agents.
		"""
		for agent1, agent2 in agent_pairs:
			agent1.load_solver()
			agent2.load_solver()
			valid_pair = self._play_match(agent1, agent2)
			if not valid_pair:
				logger.debug(
					f"Agent {agent1.name} or {agent2.name} not valid. Excluding the pair from the tournament.")
				agent1.state = 'disqualified'
				agent2.state = 'disqualified'

	def _play_match(self, agent1: Agent, agent2: Agent) -> bool:
		"""
		Play a match between two agents for multiple rounds.

		Args:
			agent1 (Agent): The first agent.
			agent2 (Agent): The second agent.

		Returns:
			bool: True if both agents are valid throughout the match, False otherwise.
		"""
		for round_num in range(self.num_rounds):
			logger.debug(
				f"\nAgent {agent1.name} with {agent1.strategy_name} vs {agent2.name} with {agent2.strategy_name}, Round {round_num}.")

			# Get moves from both agents
			move_agent_1, move_agent_2 = agent1.play(), agent2.play()
			if not (move_agent_1 and move_agent_2):
				return False

			# Update payoffs based on the opponents' moves
			updated_1 = agent1.update_payoff(move_agent_2)
			updated_2 = agent2.update_payoff(move_agent_1)
			if not (updated_1 and updated_2):
				return False

		return True

	def get_winners(self) -> List[Agent]:
		"""
		Determine the winners of the tournament.

		If target payoffs are specified, winners are agents who achieved their target payoffs.
		Otherwise, winners are agents with the highest overall payoff.

		Returns:
			List[Agent]: A list of agents who are the winners.
		"""
		if self.target_payoffs:
			return self._get_winners_by_target_payoff()
		else:
			return self._get_winners_by_highest_payoff()

	def _get_winners_by_target_payoff(self) -> List[Agent]:
		"""
		Get the agents who achieved their target payoffs.

		Returns:
			List[Agent]: A list of agents who met their target payoffs.
		"""
		return [
			agent for i, agent in enumerate(self.agents)
			if agent.get_total_payoff() == self.target_payoffs[i]
		]

	def _get_winners_by_highest_payoff(self) -> List[Agent]:
		"""
		Get the agents with the highest total payoff.

		Returns:
			List[Agent]: A list of agents with the highest payoff.
		"""
		max_payoff = max(agent.get_total_payoff() for agent in self.agents)
		return [agent for agent in self.agents if agent.get_total_payoff() == max_payoff]
