from your_database_module import db  # Replace with your actual database module

class Requests(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(100), nullable=False)
    receiver = db.Column(db.String(100), nullable=False)
    status_sender = db.Column(db.String(50), nullable=False)

    def __init__(self, sender, receiver, status_sender):
        self.sender = sender
        self.receiver = receiver
        self.status_sender = status_sender
