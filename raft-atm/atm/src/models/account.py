class Account():
	"""
	Bank account maintaining related information like account balance.
	"""
	def __init__(self, balance: int = 0):
		self._balance = balance

	def _withdraw(self, withdrawal_amt: int):
		self._balance -= withdrawal_amt

	def _deposit(self, deposit_amt: int):
		self._balance += deposit_amt
	
	def get_balance(self) -> int:
		return self._balance

	def _display_balance(self):
		print(f"Your current balance is Rs. {self._balance}.")