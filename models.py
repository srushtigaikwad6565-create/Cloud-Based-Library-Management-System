
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    available = db.Column(db.Boolean, default=True, nullable=False)


class Issue(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    book_id = db.Column(
        db.Integer,
        db.ForeignKey('book.id'),
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False
    )

    issued_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    returned_at = db.Column(db.DateTime, nullable=True)

    book = db.relationship('Book')
    user = db.relationship('User')
