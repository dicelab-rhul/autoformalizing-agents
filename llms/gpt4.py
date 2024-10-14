from src.base_llm import BaseLLM
from src.setup_logger import logger
from openai import OpenAI


class GPT4(BaseLLM):
	"""
	GPT-4 class for managing interactions specific to the GPT-4 model.
	"""

	def __init__(self, save_history=False, temperature=1, model="gpt-4o", context=None):
		"""
		Initialize the GPT-4 model.

		Args:
			save_history (bool): Should the history of the conversation be retained in subsequent prompts.
			temperature (int): GPT's temperature parameter value
			model (str): GPT model name
			context (str): Content message content
		"""
		super().__init__()
		self.client = OpenAI()
		self._save_history = save_history
		self.temperature = temperature
		self.model = model
		self._context = context
		self.__set_messages()

	@property
	def save_history(self):
		return self._save_history

	@property
	def context(self):
		return self._context

	def prompt(self, instruction, max_tokens=1024) -> str:
		"""
		Prompt the language model with an instruction and return the response.

		Args:
			instruction (str): The instruction to prompt the language model with.
			max_tokens (int): Maximum number of tokens to generate in the response.

		Returns:
			str: The response from the language model.
		"""
		#logger.debug(f"instruction: {instruction}")
		wrapped_message = {"role": "user", "content": instruction}
		# Construct message for prompt
		if not self.save_history:
			self.__set_messages()
		self.messages.append(wrapped_message)

		# Generate response from GPT-4
		response = self.client.chat.completions.create(
			model=self.model,
			messages=self.messages,
			max_tokens=max_tokens,
			temperature=self.temperature
		)
		# Extract and return the response content
		content = response.choices[0].message.content
		#logger.debug(f"response: {content}")
		return content

	def add_response(self, response):
		wrapped_response = {"role": "assistant", "content": response}
		self.messages.append(wrapped_response)

	def __set_messages(self):
		"""
		Method to handle the context message.
		"""
		if self._context is not None:
			self.messages = [{"role": "system", "content": self._context}]
		else:
			self.messages = []

	def clear_context(self):
		"""
		Method to clear context of the conversation.
		"""
		self.__set_messages()

	def get_name(self):
		"""
		Method to get name of a model.
		"""
		return self.model
