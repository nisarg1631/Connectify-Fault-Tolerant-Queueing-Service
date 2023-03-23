from src import db

class Topic(db.Model):
    __tablename__ = "topic"
    name = db.Column(db.String(256), primary_key=True, index=True)
    partitions = db.Column(db.Integer, nullable=False)