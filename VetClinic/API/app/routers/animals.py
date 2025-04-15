from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.schemas.animal import Animal, AnimalCreate, AnimalUpdate
from app.crud import animal_crud
from app.core.database import get_db 

router = APIRouter(
    prefix="/animals",
    tags=["animals"]
)

@router.post("/", response_model=Animal, status_code=status.HTTP_201_CREATED)
def create_animal(animal: AnimalCreate, db: Session = Depends(get_db)):
    return animal_crud.create_animal(db, animal)

@router.get("/", response_model=List[Animal])
def read_animals(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    animals = animal_crud.get_animals(db, skip=skip, limit=limit)
    return animals

@router.get("/{animal_id}", response_model=Animal)
def read_animal(animal_id: int, db: Session = Depends(get_db)):
    db_animal = animal_crud.get_animal(db, animal_id)
    if db_animal is None:
        raise HTTPException(status_code=404, detail="Animal not found")
    return db_animal

@router.put("/{animal_id}", response_model=Animal)
def update_animal(animal_id: int, animal: AnimalUpdate, db: Session = Depends(get_db)):
    db_animal = animal_crud.update_animal(db, animal_id, animal)
    if db_animal is None:
        raise HTTPException(status_code=404, detail="Animal not found")
    return db_animal

@router.delete("/{animal_id}", response_model=Animal)
def delete_animal(animal_id: int, db: Session = Depends(get_db)):
    db_animal = animal_crud.delete_animal(db, animal_id)
    if db_animal is None:
        raise HTTPException(status_code=404, detail="Animal not found")
    return db_animal
