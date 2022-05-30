from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

from sqlalchemy import null

 
db = SQLAlchemy()

class Rooms(db.Model):
    __tablename__ = "Rooms"
    ID = db.Column(db.Integer, primary_key=True)
    Name = db.Column('Name', db.String(80), unique = False)
    Rooms = db.Column('Rooms', db.String(80), unique = False)
    Recipient = db.Column('Recipient', db.String(80), unique = False)

    def __init__(self, Name, Rooms, Recipient):
        
        self.Name = Name
        self.Rooms = Rooms
        self.Recipient = Recipient
        
 

    # def __repr__(self):
    #     return dict(name = self.Name, room = self.Rooms, recipient = self.Recipient )

    

        



class History(db.Model):
    __tablename__ = "History"
    ID = db.Column(db.Integer, primary_key=True)
    Name = db.Column('Name', db.String(80), unique = False)
    Message = db.Column('Message', db.String(500), unique = False)
    Session = db.Column('Session', db.String(500), unique = False)
    Time = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, Name, Message, Session, Time):
        
        self.Name = Name
        self.Message = Message
        self.Session = Session
        self.Time = Time
 

    def __repr__(self):
        return f"{self.Time} : {self.Name} : {self.Message}"


class User(db.Model, UserMixin):
    __tablename__ = "user"
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(300), nullable=False, unique=True)

class Events_model(db.Model):
    __tablename__ = 'event_errors'

    id = db.Column(db.Integer, primary_key=True)
    level = db.Column(db.String(80))
    date_time = db.Column(db.DateTime, default=datetime.utcnow)
    source = db.Column(db.String(80))
    event_id = db.Column(db.Integer())

    def __init__(self, level,date_time,source,event_id):
        self.level = level
        self.date_time = date_time
        self.source = source
        self.event_id = event_id
 

    def __repr__(self):
        return f"{self.id}:{self.level}:{self.date_time}:{self.source}:{self.event_id}"