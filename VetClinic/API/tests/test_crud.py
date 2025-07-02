import pytest
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from vetclinic_api.core.database import Base

# Schemas
from vetclinic_api.schemas.animal import AnimalCreate, AnimalUpdate
from vetclinic_api.schemas.facility import FacilityCreate, FacilityUpdate
from vetclinic_api.schemas.users import (
    ClientCreate, ConsultantCreate, DoctorCreate, UserUpdate
)
from vetclinic_api.schemas.appointment import AppointmentCreate, AppointmentUpdate
from vetclinic_api.schemas.invoice import InvoiceCreate
from vetclinic_api.schemas.weight_logs import WeightLogCreate
from vetclinic_api.schemas.medical_records import MedicalRecordCreate, MedicalRecordUpdate

# CRUD modules
import vetclinic_api.crud.animal_crud as animal_crud
import vetclinic_api.crud.facility_crud as facility_crud
import vetclinic_api.crud.consultants as consultants
import vetclinic_api.crud.doctors as doctors
import vetclinic_api.crud.users_crud as users_crud
import vetclinic_api.crud.appointments_crud as appointments_crud
import vetclinic_api.crud.invoice_crud as invoice_crud
import vetclinic_api.crud.weight_log_crud as weight_log_crud
import vetclinic_api.crud.blockchain_crud as blockchain_crud
import vetclinic_api.crud.medical_records as medical_records


# ─── fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def engine():
    # baza w pamięci
    eng = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=eng)
    return eng

@pytest.fixture
def db(engine) -> Session:
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()


# ─── animal_crud tests ───────────────────────────────────────────────────────

def test_animal_crud(db):
    # create without microchip
    a1 = animal_crud.create_animal(db, AnimalCreate(
        name="Rex",
        species="Dog",
        birthday=datetime(2020,1,1),
        microchip_number=None,
        owner_id=1
    ))
    assert a1.name == "Rex" and a1.microchip_number is None

    # create with valid microchip
    chip = "9"*15
    a2 = animal_crud.create_animal(db, AnimalCreate(
        name="Mia",
        species="Cat",
        birthday=datetime(2021,5,5),
        microchip_number=chip,
        owner_id=2
    ))
    assert a2.microchip_number == chip

    # invalid microchip → ValueError
    with pytest.raises(ValueError):
        animal_crud.create_animal(db, AnimalCreate(
            name="Bad",
            species="Dog",
            birthday=datetime(2019,3,3),
            microchip_number="123",
            owner_id=3
        ))

    # get / list
    assert animal_crud.get_animal(db, a1.id).id == a1.id
    assert any(x.id == a2.id for x in animal_crud.get_animals(db))

    # update name
    updated = animal_crud.update_animal(db, a1.id, AnimalUpdate(name="Rexie"))
    assert updated.name == "Rexie"

    # update invalid chip → ValueError
    with pytest.raises(ValueError):
        animal_crud.update_animal(db, a1.id, AnimalUpdate(microchip_number="bad"))

    # delete
    deleted = animal_crud.delete_animal(db, a1.id)
    assert deleted.id == a1.id
    assert animal_crud.get_animal(db, a1.id) is None


# ─── facility_crud tests ─────────────────────────────────────────────────────

def test_facility_crud(db):
    # initially empty
    assert facility_crud.get_facilities(db) == []

    f = facility_crud.create_facility(db, FacilityCreate(
        name="Main Clinic",
        address="123 Vet St"
    ))
    assert f.name == "Main Clinic" and f.address == "123 Vet St"

    # get / list
    assert facility_crud.get_facility(db, f.id).id == f.id
    assert f in facility_crud.get_facilities(db)

    # update
    f2 = facility_crud.update_facility(db, f.id, FacilityUpdate(address="456 New Ave"))
    assert f2.address == "456 New Ave"
    assert facility_crud.update_facility(db, 999, FacilityUpdate(name="X")) is None

    # delete
    facility_crud.delete_facility(db, f.id)
    assert facility_crud.get_facility(db, f.id) is None


# ─── consultants_crud tests ──────────────────────────────────────────────────

def test_consultants_crud(db, monkeypatch):
    from vetclinic_api.services.email_service import EmailService
    monkeypatch.setattr(EmailService, "send_temporary_password", lambda e,p: None)

    # create with unique emails
    c1 = consultants.create_consultant(db, ConsultantCreate(
        first_name="Anna",
        last_name="K",
        facility_id=1,
        backup_email="b@vet.pl",
        email="anna@vet.pl"
    ))
    assert c1.email == "anna@vet.pl" and c1.must_change_password

    c2 = consultants.create_consultant(db, ConsultantCreate(
        first_name="Anna",
        last_name="K",
        facility_id=1,
        backup_email="b2@vet.pl",
        email="anna2@vet.pl"
    ))
    assert c2.email != c1.email and c2.id != c1.id

    # list / get
    all_c = consultants.list_consultants(db)
    assert c1 in all_c and c2 in all_c
    assert consultants.get_consultant(db, c1.id) == c1
    assert consultants.get_consultant(db, 0) is None

    # update (wallet_address wymagane)
    u = consultants.update_consultant(db, c1.id, UserUpdate(
        password="NewP@ss1",
        first_name="Ania",
        wallet_address="0xAAA"
    ))
    assert u.first_name == "Ania" and not u.must_change_password

    # delete
    assert consultants.delete_consultant(db, c1.id)
    assert consultants.get_consultant(db, c1.id) is None

# ─── doctors_crud tests ──────────────────────────────────────────────────────

def test_doctors_crud(db, monkeypatch):
    from vetclinic_api.services.email_service import EmailService
    monkeypatch.setattr(EmailService, "send_temporary_password", lambda e,p: None)

    raw_pw, d1 = doctors.create_doctor(db, DoctorCreate(
        first_name="Jan",
        last_name="Nowak",
        email="jan@vet.pl",
        backup_email="bk@vet.pl",
        specialization="Surgery",
        permit_number="12345",
        facility_id=1
    ))
    assert isinstance(raw_pw, str) and d1.must_change_password

    # list / get
    assert d1 in doctors.list_doctors(db)
    assert doctors.get_doctor(db, d1.id) == d1
    assert doctors.get_doctor(db, 0) is None

    # update (add wallet_address)
    d2 = doctors.update_doctor(db, d1.id, UserUpdate(
        backup_email="new@vet.pl",
        specialization="Dentistry",
        permit_number="54321",
        facility_id=2,
        password="XyZ!234",
        first_name="Janek",
        last_name="K",
        email="janek@vet.pl",
        wallet_address="0xDOC"
    ))
    assert d2.backup_email == "new@vet.pl" and d2.facility_id == 2

    # delete
    assert doctors.delete_doctor(db, d1.id)
    assert doctors.get_doctor(db, d1.id) is None


# ─── users_crud tests ────────────────────────────────────────────────────────

def test_users_crud(db, monkeypatch):
    from vetclinic_api.services.email_service import EmailService
    monkeypatch.setattr(EmailService, "send_temporary_password", lambda e,p: None)

    c = users_crud.create_client(db, ClientCreate(
        first_name="Basia",
        last_name="K",
        email="basia@c.pl",
        password="P@ssw0rd",
        phone_number="+48123456789",
        address="Addr 5",
        postal_code="00-001 Warszawa",
        role="client",
        wallet_address="0xABC"
    ))
    assert c.first_name == "Basia" and c.must_change_password

    # list / get
    clients = users_crud.list_clients(db)
    assert any(cli.id == c.id for cli in clients)
    assert users_crud.get_client(db, c.id) == c

    # update (wallet_address wymagane)
    u = users_crud.update_client(db, c.id, UserUpdate(
        password="New!234",
        first_name="Basiunia",
        phone_number="+48100000000",
        address="New Addr",
        postal_code="01-111 City",
        wallet_address="0xDEF"
    ))
    assert u.first_name == "Basiunia"

    # delete
    assert users_crud.delete_client(db, c.id)
    assert users_crud.get_client(db, c.id) is None


# ─── appointments_crud tests ──────────────────────────────────────────────────

def test_appointments_crud(db, monkeypatch):
    # stub invoice + blockchain
    monkeypatch.setattr(appointments_crud, "create_invoice", lambda db,i: None)
    monkeypatch.setattr(appointments_crud, "blockchain_add_record", lambda i,h: "0xTXX")

    now = datetime.utcnow()
    appt = appointments_crud.create_appointment(db, AppointmentCreate(
        owner_id=1,
        animal_id=2,
        visit_datetime=now,
        fee=Decimal("150.00"),
        doctor_id=7,         
        facility_id=3        
    ))
    assert appt.tx_hash == "0xTXX"

    # get / list
    assert appointments_crud.get_appointment(db, appt.id).id == appt.id
    assert appt in appointments_crud.get_appointments(db)

    # update
    up = appointments_crud.update_appointment(db, appt.id, AppointmentUpdate(fee=Decimal("200.00")))
    assert up.fee == Decimal("200.00")

    # by owner / delete
    assert appt in appointments_crud.get_appointments_by_owner(db, 1)
    rem = appointments_crud.delete_appointment(db, appt.id)
    assert rem.id == appt.id
    assert appointments_crud.get_appointment(db, appt.id) is None


# ─── invoice_crud tests ──────────────────────────────────────────────────────

def test_invoice_crud(db):
    inv = invoice_crud.create_invoice(db, InvoiceCreate(client_id=10, amount=Decimal("99.99")))
    assert inv.client_id == 10 and inv.amount == Decimal("99.99")
    assert invoice_crud.get_invoice(db, inv.id).id == inv.id
    assert inv in invoice_crud.list_invoices(db)
    up = invoice_crud.update_invoice_status(db, inv.id, "PAID")
    assert up.status == "PAID"


# ─── weight_log_crud tests ──────────────────────────────────────────────────

def test_weight_log_crud(db):
    wl = weight_log_crud.create_weight_log(db, WeightLogCreate(
        animal_id=5,
        weight=12.3,
        recorded_at=None
    ))
    assert wl.animal_id == 5 and float(wl.weight) == 12.3
    assert weight_log_crud.get_weight_log(db, wl.id).id == wl.id
    assert wl in weight_log_crud.list_weight_logs(db)
    rem = weight_log_crud.delete_weight_log(db, wl.id)
    assert rem.id == wl.id
    assert weight_log_crud.get_weight_log(db, wl.id) is None


# ─── blockchain_crud tests ───────────────────────────────────────────────────

def test_blockchain_crud(monkeypatch):
    # stub provider.get
    class DummyRec:
        def __init__(self, tx): self.transactionHash = tx
    class DummyW3:
        def __init__(self): self.eth = self
        def wait_for_transaction_receipt(self, tx): return DummyRec(b"\x01\x02")
    class DummyContract:
        def __init__(self):
            self.functions = self
        def addRecord(self, i, h): return self
        def updateRecord(self, i, h): return self
        def deleteRecord(self, i): return self
        def getRecord(self, i):
            class C: 
                def call(self): return (i, "DATA", 123, False)
            return C()
        def getRecordsByOwner(self, o):
            class C:
                def call(self): return [7,8,9]
            return C()
        def transact(self, arg): return b"\x01\x02"

    monkeypatch.setattr(blockchain_crud._provider, "get",
                        lambda: (DummyContract(), "0xACC", DummyW3()))

    # add
    tx1 = blockchain_crud.add_record(1, "H")
    assert isinstance(tx1, str)

    # get
    rec = blockchain_crud.get_record(2)
    assert rec[0] == 2

    # update
    tx2 = blockchain_crud.update_record(3, "NH")
    assert isinstance(tx2, str)

    # delete
    tx3 = blockchain_crud.delete_record(4)
    assert isinstance(tx3, str)

    # by owner
    lst = blockchain_crud.get_records_by_owner("ownerX")
    assert lst == [7,8,9]


# ─── medical_records_crud tests ──────────────────────────────────────────────

def test_medical_records_crud(db, monkeypatch):
    # stub DB lookups
    monkeypatch.setattr(medical_records, "get_appointment", lambda db,i: True)
    monkeypatch.setattr(medical_records, "get_animal", lambda db,i: True)
    # stub on‐chain CRUD
    monkeypatch.setattr(medical_records.blockchain_crud, "add_record",    lambda i,h: "TX1")
    monkeypatch.setattr(medical_records.blockchain_crud, "update_record", lambda i,h: "TX2")
    monkeypatch.setattr(medical_records.blockchain_crud, "delete_record", lambda i:   "TX3")
    # stub provider.get
    class DummyC:
        def __init__(self): self.functions = self
        def getRecordsByOwner(self, owner):
            class C: 
                def call(self): return [11,22]
            return C()
    monkeypatch.setattr(medical_records.provider, "get", lambda: (DummyC(), None, None))

    mr = medical_records.create_medical_record(db, MedicalRecordCreate(
        appointment_id=1,
        animal_id=1,
        description="Desc",
        diagnosis="Diag",
        treatment="Treat"
    ))
    assert mr["blockchain_tx"] == "TX1"
    rid = mr["id"]

    # get / not found
    assert medical_records.get_medical_record(db, rid).id == rid
    with pytest.raises(Exception):
        medical_records.get_medical_record(db, 0)

    # list / by owner
    assert any(r.id == rid for r in medical_records.list_medical_records(db))
    assert medical_records.get_records_by_owner("x") == [11,22]

    # update
    upd = medical_records.update_medical_record(db, rid, MedicalRecordUpdate(description="New"))
    assert upd["blockchain_tx"] == "TX2"

    # delete
    assert medical_records.delete_medical_record(db, rid) == "TX3"
    with pytest.raises(Exception):
        medical_records.get_medical_record(db, rid)
