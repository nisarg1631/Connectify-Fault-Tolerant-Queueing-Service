from pysyncobj import SyncObjConsumer, replicated, replicated_sync
from src.models import Account
from src import db
from typing import Dict
import uuid



class AccountsDict(SyncObjConsumer):
	"""
	Replicated accounts maintaining dictionary. 
	"""
	def __init__(self):
		super(AccountsDict, self).__init__()
		self._accounts : Dict[str,Account] = {}

	def init_from_db(self):
		for account_id in db.getall():
			self._accounts[account_id] = Account(db.get(account_id))

	def __setitem__(self, key: str, value: Account):
		"""Set value for specified key"""
		self._accounts[key] = value
	
	def __getitem__(self, key: str) -> Account:
		"""Return value for given key"""
		return self._accounts[key]
	
	def __len__(self) -> int:
		"""Return size of dict"""
		return len(self._accounts)
	
	def __contains__(self, key: str) -> bool:
		"""True if key exists"""
		return key in self._accounts
	
	@replicated_sync
	def _withdraw_impl(self, account_id: str, withdrawal_amt: int):
		self._accounts[account_id]._withdraw(withdrawal_amt=withdrawal_amt)

	@replicated_sync
	def _deposit_impl(self, account_id: str, deposit_amt: int):
		self._accounts[account_id]._deposit(deposit_amt=deposit_amt)

	@replicated_sync
	def _transfer_impl(self, from_account_id: str, to_account_id: str, transfer_amt: int):
		self._accounts[from_account_id]._withdraw(withdrawal_amt=transfer_amt)
		self._accounts[to_account_id]._deposit(deposit_amt=transfer_amt)

	@replicated_sync
	def _update_db(self, key: str, value: int):
		db.set(key, value)

	@replicated_sync
	def _create_account(self, account_id: str):
		self._accounts[account_id] = Account()

	def withdraw(self, account_id: str, withdrawal_amt: int):
		"""
		Withdraw amount from the given account_id. Disallow if insufficient balance.
		"""
		if(withdrawal_amt > self._accounts[account_id].get_balance()):
			raise Exception("Insufficient balance.")


		self._withdraw_impl(account_id=account_id, withdrawal_amt=withdrawal_amt)
		self._update_db(account_id, self._accounts[account_id].get_balance())

	def deposit(self, account_id: str, deposit_amt: int):
		"""
		Deposit amount to the given account_id.
		"""
		self._deposit_impl(account_id=account_id, deposit_amt=deposit_amt)
		self._update_db(account_id, self._accounts[account_id].get_balance())

	def transfer(self, from_account_id: str, to_account_id: str, transfer_amt: int):
		"""
		Transfer amount from an account_id to another one. Disallow if insufficient balance.
		"""
		if(transfer_amt > self._accounts[from_account_id].get_balance()):
			raise Exception("Insufficient balance.")
		if(to_account_id not in self._accounts):
				raise Exception("Account you are trying to transfer to doesn't exist.")
		
		self._transfer_impl(from_account_id=from_account_id, to_account_id=to_account_id, transfer_amt=transfer_amt)
		self._update_db(from_account_id, self._accounts[from_account_id].get_balance())
		self._update_db(to_account_id, self._accounts[to_account_id].get_balance())

	def display_balance(self, account_id: str):
		"""
		Display current account balance.
		"""
		self._accounts[account_id]._display_balance()

	def create_account(self) -> str:
		account_id = str(uuid.uuid4().hex)
		self._create_account(account_id)
		self._update_db(account_id, self._accounts[account_id].get_balance())
		return account_id