from sqlalchemy.orm import Session
from passlib.context import CryptContext

from vetclinic_api.models.users import Client
from vetclinic_api.schemas.users import ClientCreate, UserUpdate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_client(db: Session, client_in: ClientCreate) -> Client:
    """
    Tworzy nowego klienta.
    """
    hashed = get_password_hash(client_in.password)
    client = Client(
        first_name   = client_in.first_name,
        last_name    = client_in.last_name,
        email        = client_in.email,
        password_hash= hashed,
        phone_number = client_in.phone_number,
        address      = client_in.address,
        postal_code  = client_in.postal_code,
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return client

def list_clients(db: Session) -> list[Client]:
    """
    Zwraca listę wszystkich klientów.
    """
    return db.query(Client).all()

def get_client(db: Session, client_id: int) -> Client | None:
    """
    Pobiera klienta po ID.
    """
    return db.query(Client).get(client_id)

def update_client(db: Session, client_id: int, data_in: UserUpdate) -> Client | None:
    """
    Aktualizuje istniejącego klienta. Hashuje nowe hasło, jeśli podano.
    """
    client = get_client(db, client_id)
    if not client:
        return None
    data = data_in.model_dump(exclude_unset=True)
    if "password" in data:
        data["password_hash"] = get_password_hash(data.pop("password"))
    for field, value in data.items():
        setattr(client, field, value)
    db.commit()
    db.refresh(client)
    return client

def delete_client(db: Session, client_id: int) -> bool:
    """
    Usuwa klienta. Zwraca True, jeśli usunięto.
    """
    client = get_client(db, client_id)
    if not client:
        return False
    db.delete(client)
    db.commit()
    return True
