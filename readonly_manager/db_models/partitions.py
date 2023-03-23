from src import db

class Partition(db.Model):
    __tablename__ = "partition"
    ind = db.Column(db.Integer, primary_key=True)
    topic_name = db.Column(
        db.String(256),
        db.ForeignKey("topic.name"),
        nullable=False,
        primary_key=True,
    )
    broker_host = db.Column(db.String, nullable=False)
    __table_args__ = tuple(
        db.UniqueConstraint("ind", "topic_name", name="ind_id_constraint")
    )