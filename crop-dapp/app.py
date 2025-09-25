import os
import json
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from models import db, User, Product
from eth_account.messages import encode_defunct
from eth_account import Account  # for signature recovery

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///crop_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.environ.get('FLASK_SECRET', 'supersecretkey')

db.init_app(app)

# Load contract ABI and address
with open('contract_abi.json', 'r') as f:
    CONTRACT_ABI = json.load(f)

CONTRACT_ADDRESS = os.environ.get('CONTRACT_ADDRESS', '0xe5381c778898d52e57f7a4cce958e7d53082311c')


# Create DB + default admin workaround for broken before_first_request
@app.before_request
def create_tables():
    if not hasattr(app, '_tables_created'):
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            admin = User(username="admin", role="admin")
            admin.set_password("admin123")
            db.session.add(admin)
            db.session.commit()
        app._tables_created = True

def current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

# ---------- Routes ----------
@app.route('/')
def home():
    user = current_user()
    return render_template('login.html', user=user)

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        role = request.form['role']
        if User.query.filter_by(username=username).first():
            flash("Username already exists")
            return redirect(url_for('register'))
        user = User(username=username, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash("Registration successful! Please login.")
        return redirect(url_for('home'))
    return render_template('register.html', user=current_user())

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        session['user_id'] = user.id
        session['role'] = user.role
        flash("Logged in")
        if user.role == 'farmer':
            return redirect(url_for('farmer_dashboard'))
        if user.role == 'consumer':
            return redirect(url_for('consumer_dashboard'))
        return redirect(url_for('admin_dashboard'))
    flash("Invalid credentials")
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# Link Wallet endpoint (verifies signature)
@app.route('/link_wallet', methods=['POST'])
def link_wallet():
    if 'user_id' not in session:
        return jsonify({"error": "login required"}), 401
    data = request.json
    message = data.get('message')
    signature = data.get('signature')
    address = data.get('address')
    if not message or not signature or not address:
        return jsonify({"error": "missing fields"}), 400

    try:
        # recover the address from the signature
        encoded = encode_defunct(text=message)
        recovered = Account.recover_message(encoded, signature=signature)
    except Exception as e:
        return jsonify({"error": "invalid signature", "detail": str(e)}), 400

    if recovered.lower() != address.lower():
        return jsonify({"error": "signature does not match address"}), 400

    # Save wallet address for the current user
    user = User.query.get(session['user_id'])
    user.wallet_address = address
    db.session.commit()
    return jsonify({"ok": True, "wallet_address": address})

# Called by frontend after successful on-chain tx to record product locally
@app.route('/record_product', methods=['POST'])
def record_product():
    if 'user_id' not in session:
        return jsonify({"error": "login required"}), 401
    data = request.json
    name = data.get('name')
    desc = data.get('description')
    qty = data.get('quantity')
    quality = data.get('quality')
    tx_hash = data.get('txHash')
    if not name or qty is None:
        return jsonify({"error": "missing fields"}), 400

    # create product in DB (we trust the frontend which already did on-chain tx)
    p = Product(
        name=name,
        description=desc,
        quantity=int(qty),
        quality=quality,
        farmer_id=session['user_id'],
        tx_hash = tx_hash
    )
    db.session.add(p)
    db.session.commit()
    return jsonify({"ok": True, "product_id": p.id})

# Farmer dashboard
@app.route('/farmer', methods=['GET'])
def farmer_dashboard():
    if session.get('role') != 'farmer':
        return redirect(url_for('home'))
    user = current_user()
    # send ABI & contract address to template for frontend to use
    return render_template('farmer.html', user=user, abi=json.dumps(CONTRACT_ABI), contract_address=CONTRACT_ADDRESS)

# Consumer dashboard
@app.route('/consumer', methods=['GET'])
def consumer_dashboard():
    if session.get('role') != 'consumer':
        return redirect(url_for('home'))
    user = current_user()
    return render_template('consumer.html', user=user, abi=json.dumps(CONTRACT_ABI), contract_address=CONTRACT_ADDRESS)

# Admin dashboard
@app.route('/admin', methods=['GET'])
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('home'))
    users = User.query.filter(User.role != 'admin').all()
    return render_template('admin.html', users=users, user=current_user())

@app.route('/admin/delete/<int:user_id>', methods=['GET'])
def delete_user(user_id):
    if session.get('role') != 'admin':
        return redirect(url_for('home'))
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
    return redirect(url_for('admin_dashboard'))

if __name__ == "__main__":
    app.run(debug=True)
