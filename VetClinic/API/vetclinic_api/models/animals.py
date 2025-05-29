from sqlalchemy import Column, Integer, String, Date, Float, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from vetclinic_api.core.database import Base
from vetclinic_api.models.medical_records import MedicalRecord
from vetclinic_api.models.weight_logs import WeightLog


class Animal(Base):
    __tablename__ = "animals"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("clients.id"), nullable=False, comment="ID właściciela zwierzęcia")
    name = Column(String, nullable=False, index=True, comment="Imię zwierzęcia")
    species = Column(String, nullable=False, index=True, comment="Gatunek zwierzęcia, np. pies, kot")
    breed = Column(String, nullable=True, comment="Rasa zwierzęcia, może być pusta w przypadku zwierząt mieszanych")
    gender = Column(String, nullable=True, comment="Płeć zwierzęcia, np. male, female")
    birth_date = Column(Date, nullable=True, comment="Data urodzenia zwierzęcia")
    age = Column(Float, nullable=True, comment="Wiek zwierzęcia (opcjonalnie, może być obliczany na podstawie birth_date)")
    weight = Column(Float, nullable=True, comment="Waga zwierzęcia w kg")
    microchip_number = Column(String, nullable=True, unique=True, comment="Numer mikroczipa, jeśli został wszczepiony")
    notes = Column(Text, nullable=True, comment="Dodatkowe uwagi dotyczące zwierzęcia")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="Data utworzenia rekordu")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="Data ostatniej modyfikacji rekordu")
    last_visit = Column(DateTime(timezone=True), nullable=True, comment="Data ostatniej wizyty zwierzęcia u weterynarza")
    
    owner = relationship("Client", back_populates="animals")
    appointments = relationship("Appointment", back_populates="animal")
    medical_records = relationship("MedicalRecord", back_populates="animal", cascade="all, delete-orphan",)
    weight_logs = relationship("WeightLog", back_populates="animal", cascade="all, delete-orphan")
