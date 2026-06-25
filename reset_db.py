"""
Reset Database Script
Clears all data from the ambulance database and recreates tables
"""

from app import app, db

with app.app_context():
    # Drop all tables
    db.drop_all()
    print("✓ Dropped all tables")
    
    # Recreate all tables
    db.create_all()
    print("✓ Created fresh tables")
    
    print("\nDatabase reset successfully!")
    print("Odometer will start from 0 km")
