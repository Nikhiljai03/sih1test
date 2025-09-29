
from models import db, User
from app import app

with app.app_context():
    # Find or create inspector user
    inspector = User.query.filter_by(username='inspector').first()
    if not inspector:
        inspector = User(username='inspector', role='inspector')
        inspector.set_password('inspector123')
        db.session.add(inspector)
        db.session.commit()
        print('Created inspector user.')
    else:
        inspector.role = 'inspector'
        inspector.set_password('inspector123')
        db.session.commit()
        print('Reset inspector user password and role.')
