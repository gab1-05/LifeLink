import os
import django
import random
from datetime import timedelta, date
from django.utils import timezone

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lifelink.settings")
django.setup()

from django.contrib.auth.models import User
from donors.models import DonorProfile, HospitalProfile, BloodRequest, UserProfile, Message, Notification, DonationHistory

def run():
    print("Starting comprehensive seeding...")
    
    # Keep manually registered users. Only remove previous demo/sample records.
    print("Cleaning up old sample data...")
    sample_users = User.objects.filter(
        email__endswith="@example.com"
    ) | User.objects.filter(
        email__startswith="admin@"
    ) | User.objects.filter(
        username__endswith="@lifelink.local"
    )
    sample_users.delete()
    
    blood_types = ["O+", "O-", "A+", "A-", "B+", "B-", "AB+", "AB-"]
    genders = ["M", "F"]
    urgencies = ["critical", "high", "medium", "low"]
    
    # Locations: Mumbai & surroundings
    locations = [
        {"name": "Bandra", "lat": 19.0596, "lng": 72.8295},
        {"name": "Andheri", "lat": 19.1136, "lng": 72.8697},
        {"name": "Thane", "lat": 19.2183, "lng": 72.9781},
        {"name": "Navi Mumbai", "lat": 19.0330, "lng": 73.0297},
        {"name": "Sion", "lat": 19.0380, "lng": 72.8538},
        {"name": "Borivali", "lat": 19.2288, "lng": 72.8541},
        {"name": "Colaba", "lat": 18.9067, "lng": 72.8147},
        {"name": "Powai", "lat": 19.1176, "lng": 72.9060},
        {"name": "Juhu", "lat": 19.1050, "lng": 72.8263},
        {"name": "Dadar", "lat": 19.0178, "lng": 72.8478},
    ]

    first_names = ["Aarav", "Priya", "Rohit", "Sneha", "Vikram", "Ananya", "Karthik", "Ishani", "Arjun", "Meera", "Siddharth", "Tara", "Rohan", "Zara", "Aditya", "Riya", "Kabir", "Sana", "Yash", "Kyra"]
    last_names = ["Sharma", "Mehta", "Verma", "Singh", "Patel", "Reddy", "Iyer", "Kapoor", "Joshi", "Khan", "Deshmukh", "Nair", "Gupta", "Malhotra", "Bose"]

    # 1. Create Donors (40 donors)
    print("Creating 40 donors...")
    donors = []
    for i in range(40):
        fn = random.choice(first_names)
        ln = random.choice(last_names)
        email = f"{fn.lower()}.{ln.lower()}{i}@example.com"
        username = email
        
        user = User.objects.create_user(username=username, email=email, password="password", first_name=fn, last_name=ln)
        UserProfile.objects.create(user=user, phone=f"9{random.randint(100000000, 999999999)}", user_type="donor", is_verified=True)
        
        loc = random.choice(locations)
        # Add slight jitter to lat/lng
        lat = loc["lat"] + (random.random() - 0.5) * 0.05
        lng = loc["lng"] + (random.random() - 0.5) * 0.05
        
        dp = DonorProfile.objects.create(
            user=user,
            blood_type=random.choice(blood_types),
            date_of_birth=date(1980 + random.randint(0, 25), random.randint(1, 12), random.randint(1, 28)),
            gender=random.choice(genders),
            latitude=lat,
            longitude=lng,
            address=f"{loc['name']}, Mumbai",
            total_donations=random.randint(0, 8),
            rating_total=random.randint(18, 25),
            rating_count=5,
            availability_status=random.choice([True, True, True, False]), # 75% available
            last_donation_date=date.today() - timedelta(days=random.randint(30, 200)) if random.random() > 0.5 else None
        )
        donors.append(dp)

    # 2. Create Hospitals (6 hospitals)
    print("Creating 6 hospitals...")
    hospitals_data = [
        {"name": "City General Hospital", "reg": "HOSP001", "loc": locations[1]}, # Andheri
        {"name": "Metro Care Clinic", "reg": "HOSP002", "loc": locations[4]},    # Sion
        {"name": "Lifeline Medical Center", "reg": "HOSP003", "loc": locations[2]}, # Thane
        {"name": "St. Jude Hospital", "reg": "HOSP004", "loc": locations[0]},     # Bandra
        {"name": "Apex Heart Institute", "reg": "HOSP005", "loc": locations[7]},  # Powai
        {"name": "Sunrise Children Hospital", "reg": "HOSP006", "loc": locations[3]}, # Navi Mumbai
    ]
    
    hospitals = []
    for h_info in hospitals_data:
        email = f"admin@{h_info['name'].lower().replace(' ', '')}.com"
        u = User.objects.create_user(username=email, email=email, password="password", first_name=h_info['name'], last_name="Admin")
        UserProfile.objects.create(user=u, phone=f"8{random.randint(100000000, 999999999)}", user_type="hospital", is_verified=True)
        
        hp = HospitalProfile.objects.create(
            user=u,
            hospital_name=h_info['name'],
            registration_number=h_info['reg'],
            latitude=h_info['loc']['lat'],
            longitude=h_info['loc']['lng'],
            address=f"{h_info['loc']['name']}, Mumbai",
            phone_emergency=f"022-{random.randint(2000000, 2999999)}"
        )
        hospitals.append(hp)

    # 3. Create Blood Requests (15 requests)
    print("Creating 15 blood requests...")
    patients = ["Ramesh", "Sita", "Abdul", "John", "Deepa", "Rahul", "Fatima", "George", "Kiran", "Lata"]
    for i in range(15):
        h = random.choice(hospitals)
        bt = random.choice(blood_types)
        urg = random.choice(urgencies)
        status = "pending"
        if i < 3: status = "matched"
        if i < 1: status = "completed"
        
        BloodRequest.objects.create(
            hospital=h,
            patient_name=f"{random.choice(patients)} {random.choice(last_names)}",
            required_blood_type=bt,
            quantity=random.randint(1, 5),
            urgency=urg,
            status=status,
            latitude=h.latitude,
            longitude=h.longitude,
            deadline=timezone.now() + timedelta(days=random.randint(1, 3))
        )

    # 4. Create some Messages
    print("Creating sample messages...")
    for i in range(5):
        d = random.choice(donors)
        h = random.choice(hospitals)
        Message.objects.create(sender=h.user, receiver=d.user, content=f"Hello {d.user.first_name}, we need {d.blood_type} blood urgently. Can you help?", is_read=random.choice([True, False]))
        Message.objects.create(sender=d.user, receiver=h.user, content="Yes, I'm on my way.", is_read=True)

    # 5. Create some Notifications
    print("Creating notifications...")
    for d in donors[:10]:
        Notification.objects.create(user=d.user, title="Urgent Request Nearby", message="A new request for your blood type has been posted near you.", notification_type="request")
    
    for h in hospitals:
        Notification.objects.create(user=h.user, title="Donor Matched", message="A donor has been matched for your recent request.", notification_type="match")

    print("\nSeeding completed successfully!")
    print(f"Total Users: {User.objects.count()}")
    print(f"Total Donors: {DonorProfile.objects.count()}")
    print(f"Total Hospitals: {HospitalProfile.objects.count()}")
    print(f"Total Requests: {BloodRequest.objects.count()}")
    print("\nLogins:")
    print(f"  Donor: {donors[0].user.email} / password")
    print(f"  Hospital: {hospitals[0].user.email} / password")

if __name__ == "__main__":
    run()
