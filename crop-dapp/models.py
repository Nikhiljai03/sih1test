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
    fertilizer = db.Column(db.String(120))
    organic = db.Column(db.String(20))
    soil = db.Column(db.String(80))
    irrigation = db.Column(db.String(80))
    farmer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tx_hash = db.Column(db.String(200), nullable=True)  # blockchain tx hash
    assigned_transporter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    assigned_transporter = db.relationship("User", foreign_keys=[assigned_transporter_id])
    farmer = db.relationship("User", backref="products", foreign_keys=[farmer_id])


class QualityInspection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    inspector_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    grade = db.Column(db.String(20))
    certificate = db.Column(db.String(120))
    ml_score = db.Column(db.Float)
    comments = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())

    product = db.relationship('Product', backref='inspections')
    inspector = db.relationship('User', backref='inspections')

# Retailer sale model
class RetailSale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    retailer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    sale_price = db.Column(db.Float, nullable=False)
    retail_details = db.Column(db.Text)
    qr_data = db.Column(db.Text)
    qr_img = db.Column(db.Text)  # base64 PNG
    tx_hash = db.Column(db.String(200), nullable=True)  # blockchain tx hash
    timestamp = db.Column(db.DateTime, server_default=db.func.now())

    product = db.relationship('Product', backref='retail_sales')
    retailer = db.relationship('User', backref='retail_sales')
