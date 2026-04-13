"""
Database Seeding Utility.
This script is a 'Utility' used to bootstrap the system with an initial administrative user.
It demonstrates how to interact with 'Services' (user_service) and 'Core' (security/database) 
outside of the standard FastAPI request lifecycle.
"""
from backend.app.core.database import SessionLocal
from backend.app.services.user_service import get_user_by_username, create_user
from backend.app.core import security


def seed_admin():
    """
    Idempotent function to create a default admin user if one does not exist.
    """
    # 1. Core Utility: Create a new database session
    db = SessionLocal()
    try:
        # 2. Service Call: Check business logic (does user exist?)
        existing = get_user_by_username(db, 'admin')
        if existing:
            print('Admin user already exists, skipping seeding.')
            return

        # 3. Security Utility: Transform raw data (hashing)
        default_password = 'Admin@123'  # change to strong password before production
        hashed_password = security.hash_password(default_password)
        
        # 4. Service Call: Execute business operation (create record)
        create_user(db, 'admin', hashed_password, role='admin')
        print('Seeded admin user: username="admin" password="Admin@123"')
        print('Change position: define strong secret + rotate credentials')
    finally:
        db.close()


if __name__ == '__main__':
    seed_admin()