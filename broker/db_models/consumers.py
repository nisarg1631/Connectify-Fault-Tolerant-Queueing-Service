from src import db


class Consumer(db.Model):
    __tablename__ = "consumer"
    id = db.Column(db.String(32), primary_key=True, index=True)
    topic_name = db.Column(
        db.String(256),nullable=False
    )
    partition_index = db.Column(db.Integer, primary_key=True)
    offset = db.Column(db.Integer, nullable=False)
    __table_args__ = (db.ForeignKeyConstraint([topic_name, partition_index],
                                           ["topic.name", "topic.partition_index"]),
                      db.UniqueConstraint("id", "partition_index", name="id_partition_index_constraint"))