import os
import json
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import qrcode
import io
import base64
from ml_quality_model import grade_crop
from models import db, User, Product, QualityInspection, RetailSale
from eth_account.messages import encode_defunct
from eth_account import Account  # for signature recovery
from sqlalchemy.orm import joinedload

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///crop_app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.environ.get('FLASK_SECRET', 'supersecretkey')

db.init_app(app)

# Load contract ABI and address
with open('contract_abi.json', 'r') as f:
    CONTRACT_ABI = json.load(f)

CONTRACT_ADDRESS = os.environ.get('CONTRACT_ADDRESS', '0x61eedc5753741826a3f29236f9675460c9a9342e')


with open('transporter_abi.json', 'r') as f:
    TRANSPORTER_ABI = json.load(f)
TRANSPORTER_CONTRACT_ADDRESS = os.environ.get('TRANSPORTER_CONTRACT_ADDRESS', '0x913c828e417c1fa7d2cd33f1ef9240011bafef1c')

# Load QualityInspectionRegistry ABI and address
with open('quality_inspection_abi.json', 'r') as f:
    QUALITY_INSPECTION_ABI = json.load(f)
QUALITY_INSPECTION_CONTRACT_ADDRESS = os.environ.get('QUALITY_INSPECTION_CONTRACT_ADDRESS', '0x39e4b7d3729642c3289007dfbdc5adb8bd73c817')


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
        # Create default inspector
        if not User.query.filter_by(username='inspector').first():
            inspector = User(username="inspector", role="inspector")
            inspector.set_password("inspector123")
            db.session.add(inspector)
            db.session.commit()
        # Remove all retailers except 'retailer', and reset password
        retailers = User.query.filter_by(role='retailer').all()
        for r in retailers:
            if r.username != 'retailer':
                db.session.delete(r)
        db.session.commit()
        retailer = User.query.filter_by(username='retailer').first()
        if not retailer:
            retailer = User(username="retailer", role="retailer")
            retailer.set_password("retailer123")
            db.session.add(retailer)
        else:
            retailer.set_password("retailer123")
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

# Retailer dashboard route
@app.route('/retailer_dashboard')
def retailer_dashboard():
    user = current_user()
    products = Product.query.all()
    return render_template('retailer.html', user=user, products=products)

# Log sale and generate QR code
@app.route('/log_sale', methods=['POST'])
def log_sale():
    data = request.get_json()
    product_id = data.get('product_id')
    sale_price = data.get('sale_price')
    retail_details = data.get('retail_details')
    # Store sale details on blockchain (placeholder, implement actual contract call)
    tx_hash = None  # TODO: integrate blockchain transaction
    # Generate QR code with product info
    qr_data = f"ProductID:{product_id}|SalePrice:{sale_price}|Details:{retail_details}"
    img = qrcode.make(qr_data)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    qr_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    # Store in DB
    retailer_id = session.get('user_id')
    sale = RetailSale(
        product_id=product_id,
        retailer_id=retailer_id,
        sale_price=sale_price,
        retail_details=retail_details,
        qr_data=qr_data,
        qr_img=qr_b64,
        tx_hash=tx_hash
    )
    db.session.add(sale)
    db.session.commit()
    return jsonify({'qr_data': qr_data, 'qr_img': qr_b64})

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        role = request.form['role'].lower()
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
        if user.role == 'retailer':
            return redirect(url_for('retailer_dashboard'))
        if user.role == 'transporter':
            return redirect(url_for('transporter_dashboard'))
        if user.role == 'inspector':
            return redirect(url_for('inspector_dashboard'))
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
    fertilizer = data.get('fertilizer')
    organic = data.get('organic')
    soil = data.get('soil')
    irrigation = data.get('irrigation')
    tx_hash = data.get('txHash')
    if not name or qty is None:
        return jsonify({"error": "missing fields"}), 400

    # create product in DB (we trust the frontend which already did on-chain tx)
    p = Product(
        name=name,
        description=desc,
        quantity=int(qty),
        quality=quality,
        fertilizer=fertilizer,
        organic=organic,
        soil=soil,
        irrigation=irrigation,
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
    # Eager load all relationships for product catalogue
    all_products = Product.query.options(
        joinedload(Product.farmer),
        joinedload(Product.inspections),
        joinedload(Product.retail_sales).joinedload(RetailSale.retailer)
    ).all()
    # Only show products with at least one retailer sale (QR generated)
    products = [p for p in all_products if p.retail_sales and len(p.retail_sales) > 0]
    return render_template('consumer.html', user=user, products=products, abi=json.dumps(CONTRACT_ABI), contract_address=CONTRACT_ADDRESS)

# Admin dashboard
@app.route('/admin', methods=['GET', 'POST'])
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('home'))
    users = User.query.filter(User.role != 'admin').all()
    products = Product.query.all()
    transporters = User.query.filter_by(role='transporter').all()
    return render_template('admin.html', users=users, products=products, transporters=transporters, user=current_user())

@app.route('/admin/delete/<int:user_id>', methods=['GET'])
def delete_user(user_id):
    if session.get('role') != 'admin':
        return redirect(url_for('home'))
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/assign_transporter', methods=['POST'])
def assign_transporter():
    if session.get('role') != 'admin':
        return redirect(url_for('admin_dashboard'))
    product_id = request.form.get('product_id')
    transporter_id = request.form.get('transporter_id')
    product = Product.query.get(product_id)
    transporter = User.query.get(transporter_id)
    if not product or not transporter or transporter.role != 'transporter':
        flash('Invalid product or transporter')
        return redirect(url_for('admin_dashboard'))
    product.assigned_transporter_id = transporter_id
    db.session.commit()
    flash('Transporter assigned successfully')
    return redirect(url_for('admin_dashboard'))

# Transporter dashboard
@app.route('/transporter', methods=['GET'])
def transporter_dashboard():
    if session.get('role') != 'transporter':
        return redirect(url_for('home'))
    user = current_user()
    # Only show products assigned to this transporter
    products = Product.query.options(joinedload(Product.assigned_transporter)).filter_by(assigned_transporter_id=user.id).all()
    return render_template('transporter.html', user=user, products=products, transporter_abi=json.dumps(TRANSPORTER_ABI), transporter_contract_address=TRANSPORTER_CONTRACT_ADDRESS)

# Inspector dashboard
@app.route('/inspector', methods=['GET'])
def inspector_dashboard():
    if session.get('role') != 'inspector':
        return redirect(url_for('home'))
    user = current_user()
    products = Product.query.all()
    return render_template(
        'inspector.html',
        user=user,
        products=products,
        quality_inspection_abi=json.dumps(QUALITY_INSPECTION_ABI),
        quality_inspection_contract_address=QUALITY_INSPECTION_CONTRACT_ADDRESS
    )

@app.route('/record_inspection', methods=['POST'])
def record_inspection():
    product_id = request.form['product_id']
    inspector_id = session.get('user_id')
    remarks = request.form['remarks']
    # Fetch product details for ML grading
    product = Product.query.get(product_id)
    if product:
        score, grade, certification = grade_crop(
            product.fertilizer,
            product.organic,
            product.soil,
            product.irrigation,
            product.quantity,
            product.quality
        )
    else:
        score, grade, certification = 0, 'N/A', 'N/A'
    inspection = QualityInspection(
        product_id=product_id,
        inspector_id=inspector_id,
        remarks=remarks,
        score=score,
        grade=grade,
        certification=certification
    )
    db.session.add(inspection)
    db.session.commit()
    return redirect(url_for('inspector_dashboard'))

@app.route('/ml_grade_preview')
def ml_grade_preview():
    product_id = request.args.get('product_id')
    product = Product.query.get(product_id)
    if product:
        score, grade, certification = grade_crop(
            product.fertilizer,
            product.organic,
            product.soil,
            product.irrigation,
            product.quantity,
            product.quality
        )
        return jsonify({
            'score': score,
            'grade': grade,
            'certification': certification
        })
    else:
        return jsonify({'score': 0, 'grade': 'N/A', 'certification': 'N/A'})

if __name__ == "__main__":
    app.run(debug=True)
