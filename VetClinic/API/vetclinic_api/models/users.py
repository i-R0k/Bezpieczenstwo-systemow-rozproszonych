"""
Definicje modeli SQLAlchemy odpowiadających tabelom w bazie danych.
"""

from sqlalchemy import Column, Integer, String
from vetclinic_api.core.database import Base
from sqlalchemy.orm import relationship
from sqlalchemy.types import Boolean
from sqlalchemy import DateTime

class Client(Base):
    __tablename__ = "clients"
    
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    address = Column(String, nullable=False)
    postal_code = Column(String, nullable=False)
    totp_secret = Column(String, nullable=True, default=None)
    totp_confirmed = Column(Boolean, default=False)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)

    animals = relationship("Animal", back_populates="owner")
    appointments = relationship("Appointment", back_populates="owner")


    @property
    def role(self):
        return "klient"

class Doctor(Base):
    __tablename__ = "doctors"
    
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    specialization = Column(String, nullable=False)
    permit_number = Column(String, nullable=False)
    totp_secret = Column(String, nullable=True, default=None)
    totp_confirmed = Column(Boolean, default=False)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)

    appointments = relationship("Appointment", back_populates="doctor")
    

    @property
    def role(self):
        return "lekarz"

class Consultant(Base):
    __tablename__ = "consultants"
    
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    totp_secret = Column(String, nullable=True, default=None)
    totp_confirmed = Column(Boolean, default=False)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)
    
    @property
    def role(self):
        return "konsultant"
