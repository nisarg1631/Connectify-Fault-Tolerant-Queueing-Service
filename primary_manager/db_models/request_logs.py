from src import db


class RequestLog(db.Model):
    __tablename__ = "request"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    broker_name = db.Column(db.String(256), primary_key=True, index=True)
    endpoint = db.Column(db.String(256), nullable=False)
    json_data = db.Column(db.JSON, nullable=False)
