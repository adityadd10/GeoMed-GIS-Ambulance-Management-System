"""
GeoMed Database Seeder
"""
from app import app
from extensions import db
from models import User, Ambulance

def seed():
    with app.app_context():
        # Check if users already exist
        if User.query.first():
            print("Database already seeded with users.")
            return

        print("Seeding database...")

        # Create Admin
        admin = User(name="System Admin", username="admin", role="admin")
        admin.set_password("admin123")
        db.session.add(admin)

        # Create Staff (Dispatcher)
        staff = User(name="Hospital Staff", username="staff", role="staff")
        staff.set_password("staff123")
        db.session.add(staff)

        # Create Driver
        driver = User(name="Ambulance Driver", username="driver", role="driver")
        driver.set_password("driver123")
        db.session.add(driver)

        db.session.commit()

        # Create a default ambulance assigned to the driver
        amb = Ambulance(
            vehicle_number="MH-01-AB-1234",
            driver_name="Ambulance Driver",
            driver_user_id=driver.id,
            status="available"
        )
        db.session.add(amb)
        db.session.commit()

        print("Database seeded successfully!")
        print("Credentials:")
        print("Admin: admin / admin123")
        print("Staff: staff / staff123")
        print("Driver: driver / driver123")

if __name__ == '__main__':
    seed()
