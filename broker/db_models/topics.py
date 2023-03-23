from src import db


class Topic(db.Model):
    __tablename__ = "topic"
    name = db.Column(db.String(256), primary_key=True, index=True)
    partition_index = db.Column(db.Integer, primary_key = True)
    __table_args__ = tuple(
        db.UniqueConstraint("name", "partition_index", name="topic_name_constraint")
    )