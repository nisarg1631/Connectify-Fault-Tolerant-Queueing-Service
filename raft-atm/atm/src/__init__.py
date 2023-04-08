from pysyncobj import SyncObj, SyncObjConf
import pickledb
import src.config as config

db = pickledb.load(f"db/atm-{config.REPLICA_NO}.db", True)

from src.models import AccountsDict, Account

accounts = AccountsDict()

accounts_sync_obj_conf = SyncObjConf(
	journalFile=f"journal/atm-{config.REPLICA_NO}.journal",
	fullDumpFile=f"dump/atm-{config.REPLICA_NO}.dump",
	appendEntriesUseBatch=False
)

accounts_sync_obj = SyncObj(
	selfNode=f"atm-{config.REPLICA_NO}:5000",	# My hostname + port
	otherNodes=[ f"atm-{num}:5000"for num in range(1, config.TOT_REPLICAS + 1) if num != config.REPLICA_NO ],	# Other atm"s hostname + port
	consumers=[accounts],	# Consumers subscribed to this SyncObj
	conf=accounts_sync_obj_conf	# Configuration for the SyncObj
)