#!/usr/bin/env python3
# seed_validated_data.py

import datetime
from sqlalchemy.exc import IntegrityError
from vetclinic_api.core.database      import engine, SessionLocal, Base
from vetclinic_api.crud.users_crud    import create_user
from vetclinic_api.crud.animal_crud   import create_animal
from vetclinic_api.crud.appointments_crud  import create_appointment
from vetclinic_api.crud.medical_records import create_medical_record
from vetclinic_api.crud.weight_log_crud     import create_weight_log

from vetclinic_api.schemas.users           import ClientCreate, DoctorCreate
from vetclinic_api.schemas.animal         import AnimalCreate
from vetclinic_api.schemas.appointment    import AppointmentCreate
from vetclinic_api.schemas.medical_records import MedicalRecordCreate
from vetclinic_api.schemas.weight_logs     import WeightLogCreate

from vetclinic_api.models.users       import Client, Doctor
from vetclinic_api.models.animals     import Animal
from vetclinic_api.models.appointments import Appointment
from vetclinic_api.models.medical_records import MedicalRecord
from vetclinic_api.models.weight_logs     import WeightLog

def main():
    # 1) Utwórz tabele jeśli jeszcze nie istnieją
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    print("🔧 Rozpoczynam seedowanie danych...")

    # 2) Klienci
    clients_data = [
        {
            "first_name":   "Jan", "last_name": "Kowalski",
            "email":        "jan.kowalski@mail.com",
            "password":     "tajne123", "role": "klient",
            "phone_number": "+48100100200",
            "address":      "ul. Lipowa 5",
            "postal_code":  "00-001 Warszawa"
        },
        {
            "first_name":   "Anna", "last_name": "Nowak",
            "email":        "anna.nowak@mail.com",
            "password":     "haslo456", "role": "klient",
            "phone_number": "+48500100200",
            "address":      "ul. Długa 10",
            "postal_code":  "01-002 Warszawa"
        },
        {
            "first_name":   "Piotr", "last_name": "Wiśniewski",
            "email":        "piotr.wisniewski@mail.com",
            "password":     "sekret789", "role": "klient",
            "phone_number": "+48700100200",
            "address":      "ul. Krótka 2",
            "postal_code":  "02-003 Warszawa"
        },
    ]
    for data in clients_data:
        if db.query(Client).filter_by(email=data["email"]).first():
            print(f"⏭ Klient {data['email']} już istnieje, pomijam")
            continue
        try:
            schema = ClientCreate(**data)
            user = create_user(db, schema)
            print(f"✅ Dodano klienta: {user.email} (ID={user.id})")
        except Exception as e:
            print(f"❌ Błąd dodawania klienta {data['email']}: {e}")

    # 3) Lekarze
    doctors_data = [
        {
            "first_name":   "Ewa", "last_name": "Zielińska",
            "email":        "ewa.zielinska@vetclinic.pl",
            "password":     "lek12345",  "role": "lekarz",
            "specialization": "chirurgia", "permit_number": "12345"
        },
        {
            "first_name":   "Marek", "last_name": "Wójcik",
            "email":        "marek.wojcik@vetclinic.pl",
            "password":     "lek67890", "role": "lekarz",
            "specialization": "dermatologia","permit_number": "54321"
        },
    ]
    for data in doctors_data:
        if db.query(Doctor).filter_by(email=data["email"]).first():
            print(f"⏭ Lekarz {data['email']} już istnieje, pomijam")
            continue
        try:
            schema = DoctorCreate(**data)
            doc = create_user(db, schema)
            print(f"✅ Dodano lekarza: Dr {doc.last_name} (ID={doc.id})")
        except Exception as e:
            print(f"❌ Błąd dodawania lekarza {data['email']}: {e}")

    # 4) Zwierzęta
    animals_data = [
        {
            "owner_id": 2, "name": "Burek",  "species": "Pies", "breed": "Owczarek",
            "gender": "male", "birth_date": "2020-01-05", "age": 5, "weight": 30.0,
            "microchip_number": "000123456789012", "notes": "Brak uwag"
        },
        {
            "owner_id": 3, "name": "Mruczek", "species": "Kot",  "breed": "Perski",
            "gender": "female","birth_date": "2019-06-10","age": 6,"weight": 5.2,
            "microchip_number": "000223456789012","notes": "Alergia pokarmowa"
        },
        {
            "owner_id": 2, "name": "Łatek",   "species": "Królik", "breed": "Baranek",
            "gender": "male","birth_date": "2021-03-15","age": 4,"weight": 2.4,
            "microchip_number": "000323456789012","notes": ""
        },
        {
            "owner_id": 4, "name": "Reksio",  "species": "Pies", "breed": None,
            "gender": "male","birth_date": "2018-11-20","age": 6,"weight": 22.1,
            "microchip_number": "000423456789012","notes": "Częste drapanie"
        },
    ]
    for data in animals_data:
        cond = db.query(Animal).filter_by(
            owner_id=data["owner_id"], name=data["name"]
        ).first()
        if cond:
            print(f"⏭ Zwierzę {data['name']} już istnieje, pomijam")
            continue
        try:
            schema = AnimalCreate(**data)
            ani = create_animal(db, schema)
            print(f"✅ Dodano zwierzę: {ani.name} (ID={ani.id})")
        except Exception as e:
            print(f"❌ Błąd dodawania zwierzęcia {data['name']}: {e}")

    # 5) Wizyty
    visits_data = [
        {"doctor_id":2,"animal_id":1,"owner_id":2,"visit_datetime":"2025-04-20T09:00:00",
         "reason":"Kontrola szczepienia","status":"zakończona","notes":""},
        {"doctor_id":2,"animal_id":2,"owner_id":3,"visit_datetime":"2025-04-22T14:00:00",
         "reason":"Zabieg kleszcza","status":"odwołana","notes":""},
        {"doctor_id":3,"animal_id":3,"owner_id":2,"visit_datetime":"2025-05-01T11:15:00",
         "reason":"Badanie krwi","status":"zaplanowana","notes":""},
    ]
    for data in visits_data:
        cond = db.query(Appointment).filter_by(
            animal_id=data["animal_id"], visit_datetime=data["visit_datetime"]
        ).first()
        if cond:
            print(f"⏭ Wizyta {data['visit_datetime']} już istnieje, pomijam")
            continue
        try:
            schema = AppointmentCreate(**data)
            appt = create_appointment(db, schema)
            print(f"✅ Dodano wizytę ID={appt.id}")
        except Exception as e:
            print(f"❌ Błąd dodawania wizyty {data}: {e}")

    # 6) Rekordy medyczne
    records_data = [
        {"animal_id":1,"appointment_id":1,
         "description":"Szczepienie przeciwko wściekliźnie","diagnosis":"OK","treatment":""},
        {"animal_id":2,"appointment_id":2,
         "description":"Usuwanie kleszcza z szyi","diagnosis":None,"treatment":"Antybiotyk"},
    ]
    for data in records_data:
        cond = db.query(MedicalRecord).filter_by(
            appointment_id=data["appointment_id"]
        ).first()
        if cond:
            print(f"⏭ Rekord medyczny wizyty {data['appointment_id']} już istnieje")
            continue
        try:
            schema = MedicalRecordCreate(**data)
            mr = create_medical_record(db, schema)
            print(f"✅ Dodano rekord medyczny ID={mr.id}")
        except Exception as e:
            print(f"❌ Błąd dodawania rekordu medycznego dla wizyty {data['appointment_id']}: {e}")

    # 7) Logi wagowe
    weight_logs_data = [
        {"animal_id":1,"weight":29.5},
        {"animal_id":1,"weight":30.0},
        {"animal_id":2,"weight":5.0},
        {"animal_id":3,"weight":2.3},
    ]
    for data in weight_logs_data:
        cond = db.query(WeightLog).filter_by(
            animal_id=data["animal_id"], weight=data["weight"]
        ).order_by(WeightLog.recorded_at.desc()).first()
        if cond and abs(cond.weight - data["weight"]) < 1e-6:
            print(f"⏭ Log wagi {data} już istnieje, pomijam")
            continue
        try:
            schema = WeightLogCreate(**data)
            wl = create_weight_log(db, schema)
            print(f"✅ Dodano log wagi ID={wl.id}")
        except Exception as e:
            print(f"❌ Błąd dodawania logu wagi {data}: {e}")

    db.close()
    print("🎉 Seed zakończony!")

if __name__ == "__main__":
    main()
