from sqlalchemy.orm import Session
from models.animals import Animal as AnimalModel
from schemas.animal import AnimalCreate, AnimalUpdate
from validators.animal_chip_validator import validate_animal_chip

def create_animal(db: Session, animal: AnimalCreate):
    # Jeśli numer mikroczipa jest podany, walidujemy go.
    if animal.microchip_number:
        if not validate_animal_chip(animal.microchip_number):
            raise ValueError("Numer mikroczipa musi zawierać dokładnie 15 cyfr.")

    db_animal = AnimalModel(**animal.model_dump())
    db.add(db_animal)
    db.commit()
    db.refresh(db_animal)
    return db_animal

def update_animal(db: Session, animal_id: int, animal: AnimalUpdate):
    db_animal = db.query(AnimalModel).filter(AnimalModel.id == animal_id).first()
    if not db_animal:
        return None
    update_data = animal.model_dump(exclude_unset=True)
    # Jeśli próbujemy aktualizować numer mikroczipa, również walidujemy go.
    if "microchip_number" in update_data and update_data["microchip_number"] is not None:
        if not validate_animal_chip(update_data["microchip_number"]):
            raise ValueError("Numer mikroczipa musi zawierać dokładnie 15 cyfr.")
    
    for key, value in update_data.items():
        setattr(db_animal, key, value)
    db.commit()
    db.refresh(db_animal)
    return db_animal

def get_animal(db: Session, animal_id: int):
    return db.query(AnimalModel).filter(AnimalModel.id == animal_id).first()

def get_animals(db: Session, skip: int = 0, limit: int = 100):
    return db.query(AnimalModel).offset(skip).limit(limit).all()

def delete_animal(db: Session, animal_id: int):
    db_animal = get_animal(db, animal_id)
    if not db_animal:
        return None
    db.delete(db_animal)
    db.commit()
    return db_animal
