from src import db


class Broker(db.Model):
    __tablename__ = "broker"
    name = db.Column(db.String(256), primary_key=True, index=True)
    status = db.Column(db.Integer)