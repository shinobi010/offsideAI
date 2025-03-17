from database import db

# Match Table
class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False)
    team1_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    team2_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    score_team1 = db.Column(db.Integer, default=0)
    score_team2 = db.Column(db.Integer, default=0)
    
    team1 = db.relationship("Team", foreign_keys=[team1_id])
    team2 = db.relationship("Team", foreign_keys=[team2_id])

# Team Table
class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    country = db.Column(db.String(50), nullable=True)
    players = db.relationship('Player', backref='team', lazy=True)

# Player Table
class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(50))  # e.g., Forward, Midfielder, Defender
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)

# Event Table (Tracks goals, fouls, offsides)
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey('match.id'), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    event_type = db.Column(db.String(50), nullable=False)  # Goal, Foul, Offside
    timestamp = db.Column(db.Float, nullable=False)  # Seconds into the match

# Offside Detection Table
class OffsideDetection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey('match.id'), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    position_x = db.Column(db.Float, nullable=False)  # X coordinate on the field
    position_y = db.Column(db.Float, nullable=False)  # Y coordinate on the field
    is_offside = db.Column(db.Boolean, nullable=False)  # True if offside detected
    timestamp = db.Column(db.Float, nullable=False)  # Time in match when detected
