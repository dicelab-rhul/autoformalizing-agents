from utils import generate_agent_name


class Agent:
	"""
	Represents an Agent in the tournament.

	Each agent autoformalises a game description, plays in the tournament, and updates its state.
	It also keeps track of its payoffs, choices, and opponent's choices.
	"""

	def __init__(self, game=None, strategy="tit-for-tat"):
		"""
		Initializes the Agent with a random name, an empty payoff list, choice list, and opponent's choice list.
		"""
		self.name = generate_agent_name(3)
		self.payoffs = []  # List to store the agent's payoffs over time
		self.choices = []  # List to store the agent's choices
		self.opponent_choices = []  # List to store the opponent's choices
		self.game = game
		self.strategy = strategy
		#TODO add solver object

	def init(self):
		"""
		Initializes the agent with the game.

		:return: syntactic correctness
		"""
		print(f"Agent {self.name} with strategy {self.strategy} is initializing.")
		#TODO autoformalise
		return self.verify()

	def verify(self):
		#TODO
		return True

	def play(self):
		"""
		Simulates the agent making a choice in the tournament.
		"""

		choice = None  # TODO get choice
		self.choices.append(choice)
		print(f"Agent {self.name} made choice: {choice}")

	def update(self, opponent_choice):
		"""
		Updates the agent's payoff and logs the opponent's choice.

		:param opponent_choice: The choice made by the opponent in the current round.
		"""
		self.opponent_choices.append(opponent_choice)
		payoff = 0 #  TODO calculate payoff
		self.payoffs.append(payoff)
		print(f"Agent {self.name} received payoff: {payoff} and logged opponent's choice: {opponent_choice}")

	def get_payoffs(self):
		"""
		Returns the list of payoffs accumulated by the agent.

		:return: List of payoffs.
		"""
		return self.payoffs

	def get_total_payoff(self):
		"""
		Returns the total payoff accumulated by the agent.

		:return: Total payoff.
		"""
		return sum(self.payoffs)
