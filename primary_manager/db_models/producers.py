from src import db


class Producer(db.Model):
    __tablename__ = "producer"
    id = db.Column(db.String(32), primary_key=True, index=True)
    topic_name = db.Column(
        db.String(256), db.ForeignKey("topic.name"), nullable=False
    )