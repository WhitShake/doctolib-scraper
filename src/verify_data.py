# src/verify_data.py
from database import SessionLocal
from models import Doctor

def verify_new_fields():
    """Verify that new fields are being stored correctly"""
    db = SessionLocal()
    try:
        doctors = db.query(Doctor).all()

        print("VERIFYING NEW FIELDS")
        print("=" * 50 )

        # Number of doctors accepting/not accepting new patients
        accepting_count = sum(1 for doctor in doctors if doctor.accepts_new_patients)
        not_accepting_count = sum(1 for doctor in doctors if not doctor.accepts_new_patients)

        unknown_count = len(doctors) - accepting_count - not_accepting_count

        print("ACCEPTING NEW PATIENTS STATS: ")
        print(f"Accepting: {accepting_count} doctors")
        print(f"Not accepting: {not_accepting_count} doctors")
        print(f"Unknown/Null: {unknown_count} doctors")
        print()

        # Show regulation sectors
        regulation_sectors = {}
        for doctor in doctors:
            sector = doctor.regulation_sector or 'unknown'
            regulation_sectors[sector] = regulation_sectors.get(sector, 0) + 1

        print("REGULATION SECTORS:")
        for sector, count in regulation_sectors.items():
            print(f"   {sector}: {count} doctors")
        print()

        # Show sample data
        print("SAMPLE DOCTORS")
        print("-" * 30)

        for doctor in doctors[:5]:
            print(f"Dr. {doctor.last_name}")
            print(f"  Accepts new patients: {doctor.accepts_new_patients}")
            print(f"  Regulation sector: {doctor.regulation_sector}")
            print(f"  City: {doctor.city}")
            print()
            
    finally:
        db.close()

if __name__ == "__main__":
    verify_new_fields()
