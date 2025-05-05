from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, func
from core.database import Base
from sqlalchemy.orm import relationship

class WeightLog(Base):
    __tablename__ = "weight_logs"
    id = Column(Integer, primary_key=True)
    animal_id = Column(Integer, ForeignKey("animals.id", ondelete="CASCADE"), nullable=False)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now(), comment="Kiedy zmierzono wagę")
    weight = Column(Float, nullable=False, comment="Zmierzona waga zwierzęcia")

    animal = relationship("Animal", back_populates="weight_logs")
