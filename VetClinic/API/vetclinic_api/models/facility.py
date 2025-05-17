from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from vetclinic_api.core.database import Base
from datetime import datetime, timezone

def utcnow():
    return datetime.now(timezone.utc)

class Facility(Base):
    __tablename__ = "facilities"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    appointments = relationship("Appointment", back_populates="facility")
