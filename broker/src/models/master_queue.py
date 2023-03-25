import time

from src import db
from src import TopicDB, LogDB


class MasterQueue:
    """
    Master queue is a controller for the database.
    """
    def add_topic(self, topic_name: str, partition_index:int) -> None:
        """Add a partition to the database."""
        db.session.add(TopicDB(name=topic_name, partition_index = partition_index))
        db.session.commit()

    def get_log(self, topic_name: str, partition_index: int, log_index: int) -> str:
        """Return the log at given index."""
        log = LogDB.query.filter_by(
            topic_name=topic_name, partition_index=partition_index, id=log_index
        ).first()
        if log is not None:
            return log.message
        raise Exception(f"No log found with index {log_index} in topic {topic_name} - partition {partition_index}") 

    def add_log(self, log_index: int, topic_name: str, partition_index:int, producer_id: str, message: str):
        """Add a log to the partition."""
        timestamp = time.time()
        db.session.add(
            LogDB(
                id=log_index,
                topic_name=topic_name,
                partition_index=partition_index,
                producer_id=producer_id,
                message=message,
                timestamp=timestamp,
            )
        )
        db.session.commit()
