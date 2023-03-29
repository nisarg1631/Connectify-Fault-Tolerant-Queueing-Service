from src import accounts, config, Account, accounts_sync_obj

admin_prompt = """
How may I help you?
Press 1: Create Account | Press 2: Press Anything else: Exit
"""

customer_prompt = """
How may I help you, %s ?
Press 1: Withdraw | Press 2: Deposit | Press 3: Display Balance | Press 4: Transfer | Press Anything else: Exit
"""

def main():
	accounts.init_from_db()
	print(f"ATM Machine #{config.REPLICA_NO} Up!")
	try:
		while(True):
			if config.REPLICA_NO == 1:
				ans = input("Are you a system administrator? (y/n)")
				if(ans == "y" or ans == "Y"):
					while(True):
						choice = input(admin_prompt)
						if(choice == "1"):
							account_id = accounts.create_account()
							print(f"Created account with account ID : {account_id}")
						else:
							break
					print("Closing session...")
					continue
					
			account_id = input("Dear customer, please enter your account ID: ")
			if(account_id not in accounts):
				print("Account does not exist. Closing session...")
				continue
			else:
				print(f"Welcome {account_id}!")
			
			while(True):
				choice = input(customer_prompt % (account_id))
				try:
					if(choice == "1"):
						withdrawal_amt = int(input("Enter amount to withdraw: "))
						accounts.withdraw(account_id, withdrawal_amt)
						print(accounts_sync_obj.getStatus())
						
					elif(choice == "2"):
						deposit_amt = int(input("Enter amount to deposit: "))
						accounts.deposit(account_id, deposit_amt)
						print(accounts_sync_obj.getStatus())
					elif(choice == "3"):
						accounts.display_balance(account_id)
					elif(choice == "4"):
						transfer_amt = int(input("Enter amount to transfer: "))
						transfer_account_id = input("Enter account ID to transfer to: ")
						accounts.transfer(account_id, transfer_account_id, transfer_amt)
					else:
						break
				except Exception as e:
					print(e)
				
			print("Closing session...")
			continue
	
	except KeyboardInterrupt:
		print(f"\nClosing Machine #{config.REPLICA_NO}...")

if __name__ == "__main__":
	main()