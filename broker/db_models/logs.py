from src import db


class Log(db.Model):
    __tablename__ = "log"
    id = db.Column(db.Integer, primary_key=True)
    topic_name = db.Column(
        db.String(256),
        nullable=False,
        primary_key=True,
    )
    partition_index = db.Column(db.Integer,primary_key=True)
    producer_id = db.Column(
        db.String(32),nullable=False
    )
    message = db.Column(db.String(256), nullable=False)
    timestamp = db.Column(db.Float, nullable=False)
    __table_args__ = tuple(
        db.UniqueConstraint("id", "topic_name", "partition_index",name="log_id_constraint")
    )
    ___table_args__ = (db.ForeignKeyConstraint([topic_name, partition_index],
                                           ["topic.name", "topic.partition_index"]), {})