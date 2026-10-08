"""Asistente interactivo para crear el primer superadministrador sin datos de demo."""
import getpass
import re
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.database import SessionLocal, init_db
from app.models import User
from app.security import hash_password


def create_superadmin(db, name: str, email: str, password: str) -> User:
    name, email = name.strip(), email.strip().lower()
    if not name or not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email):
        raise ValueError('Nombre y correo válidos son obligatorios')
    if len(password) < 12:
        raise ValueError('La contraseña debe tener mínimo 12 caracteres')
    if db.scalar(select(User).where(User.email == email)):
        raise ValueError('Ya existe un usuario con ese correo')
    user = User(name=name[:150], email=email[:160], password_hash=hash_password(password),
                role='superadmin', hospital_id=None, approval='approved', active=True)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ValueError('Correo duplicado')
    return user


if __name__ == '__main__':
    init_db()
    print('=== HospitalOps: crear superadministrador ===')
    name = input('Nombre completo: ')
    email = input('Correo electrónico: ')
    password = getpass.getpass('Contraseña (mínimo 12 caracteres): ')
    confirmation = getpass.getpass('Repetir contraseña: ')
    if password != confirmation:
        raise SystemExit('Las contraseñas no coinciden')
    with SessionLocal() as session:
        try:
            user = create_superadmin(session, name, email, password)
            print(f'Superadministrador creado: {user.email}. Inicia sesión y crea tu primer hospital.')
        except ValueError as exc:
            raise SystemExit(str(exc))
