from app import create_app, db
from flask import session
from app.models import User
from werkzeug.security import generate_password_hash
from datetime import timedelta

app = create_app()



#### Initating a context to add first user
with app.app_context():
    admin_user = User.query.filter_by(email="admin@pinacalabs.com").first()
    if admin_user is None:
        admin_user = User(email='admin@pinacalabs.com',
                          name='admin',
                          username='admin',
                          role='admin',
                          password=generate_password_hash('alvksn13957VAVw#f3',method='sha256'),
                          department='irctc',
                          department_role='General Manager (GM)',
                          user_pages={
                            "overview": True,
                            "suspected_pnrs": True,
                            "suspected_ip_addresses": True,
                            "suspected_users": True,
                            "suspected_number": True,
                            "ip_history": True,
                            "suspected_user_history": True,
                            "infrastructure_monitoring": True,
                            "brand_monitoring": True,
                            "booking_logs": True,
                            "user_registration_logs": True,
                            "blacklist": True,
                            "daily_status": True,
                            "reports": True,
                            "software_procurement": True,
                            "about_us": True,
                            "admin": True,
                            "casemanagement_pnr": True, 
                            "casemanagement_user": True,
                            "casemanagement_overview":True,
                            "casemanagement_ip":True 
                            },
                          user_actions={
                            "view": True, 
                            "download" :True, 
                            "upload": True, 
                            "delete": True,
                            "edit": True,
                            "block": True
                          }
                        )
        db.session.add(admin_user)
        db.session.commit()


if __name__ == "__main__":
    print('Starting Server....')
    app.run(host="0.0.0.0", port=8000, debug=True)
