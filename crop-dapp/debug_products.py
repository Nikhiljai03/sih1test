from models import db, Product
from app import app

with app.app_context():
    # Print all products and their fields for debugging
    products = Product.query.all()
    for p in products:
        print(f"ID: {p.id}, Name: {p.name}, Fertilizer: {p.fertilizer}, Organic: {p.organic}, Soil: {p.soil}, Irrigation: {p.irrigation}, Quantity: {p.quantity}, Quality: {p.quality}")
        # Check for missing or problematic fields
        missing = []
        if not p.fertilizer or not p.fertilizer.strip(): missing.append('fertilizer')
        if not p.organic or not p.organic.strip(): missing.append('organic')
        if not p.soil or not p.soil.strip(): missing.append('soil')
        if not p.irrigation or not p.irrigation.strip(): missing.append('irrigation')
        if p.quantity is None: missing.append('quantity')
        if not p.quality or not p.quality.strip(): missing.append('quality')
        if missing:
            print(f"  -> Missing fields: {', '.join(missing)}")
        else:
            print("  -> All fields present.")
    print("Done.")
