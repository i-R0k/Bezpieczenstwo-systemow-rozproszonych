from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from vetclinic_api.core.database import Base

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False, comment="ID lekarza obsługującego wizytę")
    animal_id = Column(Integer, ForeignKey("animals.id"), nullable=False, comment="ID zwierzęcia będącego pacjentem")
    owner_id = Column(Integer, ForeignKey("clients.id"), nullable=False, comment="ID właściciela zwierzęcia")
    
    visit_datetime = Column(DateTime, nullable=False, comment="Data i czas wizyty")
    reason = Column(Text, nullable=True, comment="Powód wizyty lub rodzaj usługi")
    status = Column(String, nullable=False, default="zaplanowana", comment="Status wizyty: zaplanowana, odwołana, zakończona")
    notes = Column(Text, nullable=True, comment="Dodatkowe informacje i uwagi dotyczące wizyty")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="Data utworzenia rekordu wizyty")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="Data ostatniej modyfikacji rekordu")
    
    doctor = relationship("Doctor", back_populates="appointments")
    animal = relationship("Animal", back_populates="appointments")
    owner = relationship("Client", back_populates="appointments")
    medical_records = relationship("MedicalRecord", back_populates="appointment",cascade="all, delete-orphan",)
