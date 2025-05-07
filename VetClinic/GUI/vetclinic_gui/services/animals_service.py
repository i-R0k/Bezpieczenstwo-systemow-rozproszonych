from vetclinic_api.crud.animal_crud import get_animals, get_animal, create_animal, update_animal, delete_animal
from vetclinic_api.core.database import SessionLocal
from vetclinic_api.schemas import animal as AnimalSchema

class AnimalService:
    @staticmethod
    def list():
        db = SessionLocal()
        try:
            return get_animals(db)
        finally:
            db.close()

    @staticmethod
    def get(aid: int):
        db = SessionLocal()
        try:
            return get_animal(db, aid)
        finally:
            db.close()

    @staticmethod
    def create(data: dict):
        db = SessionLocal()
        try:
            animal_in = AnimalSchema.AnimalCreate(**data)
            return create_animal(db, animal_in)
        finally:
            db.close()

    @staticmethod
    def update(aid: int, data: dict):
        db = SessionLocal()
        try:
            animal_in = AnimalSchema.AnimalUpdate(**data)
            return update_animal(db, aid, animal_in)
        finally:
            db.close()

    @staticmethod
    def delete(aid: int):
        db = SessionLocal()
        try:
            return delete_animal(db, aid)
        finally:
            db.close()
