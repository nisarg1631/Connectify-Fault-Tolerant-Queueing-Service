from src import db


class Broker(db.Model):
    __tablename__ = "broker"
    id = db.Column(db.Integer, primary_key = True, index = True)
    name = db.Column(db.String(256))
    partition_index = db.Column(db.Integer)
    broker = db.Column(db.String(256))
    port = db.Column(db.String(256))
