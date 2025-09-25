from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'farmer', 'consumer', 'admin'
    wallet_address = db.Column(db.String(100), nullable=True)  # linked wallet

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    quantity = db.Column(db.Integer)
    quality = db.Column(db.String(80))
    farmer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tx_hash = db.Column(db.String(200), nullable=True)  # blockchain tx hash

    farmer = db.relationship("User", backref="products")
