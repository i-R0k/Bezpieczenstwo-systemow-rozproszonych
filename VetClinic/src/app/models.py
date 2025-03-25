"""
Definicje modeli SQLAlchemy odpowiadających tabelom w bazie danych.
"""

from sqlalchemy import Column, Integer, String, Date, DateTime, Text, Numeric, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from ..app.database import Base
import datetime

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=True)  # Hasło w postaci hash
    role = Column(String, nullable=False)  # np. 'doctor', 'receptionist', 'owner'
    
    # Relacje
    animals = relationship("Animal", back_populates="owner")
    appointments = relationship("Appointment", back_populates="doctor")
    invoices = relationship("Invoice", back_populates="user")

class Animal(Base):
    __tablename__ = "animals"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    species = Column(String)    # np. pies, kot
    breed = Column(String)
    birth_date = Column(Date)
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    # Relacje
    owner = relationship("User", back_populates="animals")
    appointments = relationship("Appointment", back_populates="animal")

class Appointment(Base):
    __tablename__ = "appointments"
    
    id = Column(Integer, primary_key=True, index=True)
    animal_id = Column(Integer, ForeignKey("animals.id"))
    doctor_id = Column(Integer, ForeignKey("users.id"))
    date = Column(DateTime, default=datetime.datetime.utcnow)
    description = Column(Text)
    status = Column(String)  # np. 'scheduled', 'completed'
    
    # Relacje
    animal = relationship("Animal", back_populates="appointments")
    doctor = relationship("User", back_populates="appointments")
    medical_record = relationship("MedicalRecord", uselist=False, back_populates="appointment")
    invoice = relationship("Invoice", uselist=False, back_populates="appointment")

class MedicalRecord(Base):
    __tablename__ = "medical_records"
    
    id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"))
    diagnosis = Column(Text)
    treatment = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relacje
    appointment = relationship("Appointment", back_populates="medical_record")
    blockchain_hash = relationship("BlockchainHash", uselist=False, back_populates="medical_record")

class Invoice(Base):
    __tablename__ = "invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    appointment_id = Column(Integer, ForeignKey("appointments.id"))
    amount = Column(Numeric)
    paid = Column(Boolean, default=False)
    payment_date = Column(DateTime, nullable=True)
    
    # Relacje
    user = relationship("User", back_populates="invoices")
    appointment = relationship("Appointment", back_populates="invoice")

class BlockchainHash(Base):
    __tablename__ = "blockchain_hashes"
    
    id = Column(Integer, primary_key=True, index=True)
    record_id = Column(Integer, ForeignKey("medical_records.id"))
    hash = Column(Text)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relacje
    medical_record = relationship("MedicalRecord", back_populates="blockchain_hash")
