from models import db, Product
from app import app

# Default values for missing fields
def get_default(field):
    defaults = {
        'fertilizer': 'urea',
        'organic': 'organic',
        'soil': 'loamy',
        'irrigation': 'drip',
        'quantity': 1,
        'quality': 'medium',
    }
    return defaults[field]

with app.app_context():
    products = Product.query.all()
    for p in products:
        changed = False
        if not p.fertilizer or not p.fertilizer.strip():
            p.fertilizer = get_default('fertilizer')
            changed = True
        if not p.organic or not p.organic.strip():
            p.organic = get_default('organic')
            changed = True
        if not p.soil or not p.soil.strip():
            p.soil = get_default('soil')
            changed = True
        if not p.irrigation or not p.irrigation.strip():
            p.irrigation = get_default('irrigation')
            changed = True
        if p.quantity is None:
            p.quantity = get_default('quantity')
            changed = True
        if not p.quality or not p.quality.strip():
            p.quality = get_default('quality')
            changed = True
        if changed:
            print(f"Fixed product ID {p.id}")
    db.session.commit()
print("All products checked and fixed if needed.")
