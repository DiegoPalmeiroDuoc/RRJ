"""HospitalOps web application. Server-rendered views + JSON dashboard endpoint."""
import csv
import io
import os
import re
import secrets
from decimal import Decimal, InvalidOperation
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from app.database import get_db, init_db, SessionLocal
from app.models import (
    Hospital, Department, User, Asset, Ticket, TicketComment,
    InventoryItem, InventoryMovement, StockCount, StockCountLine,
    CRMContact, CRMOpportunity, AuditLog, now,
)
from app.security import hash_password, verify_password

BASE = os.path.dirname(__file__)


@asynccontextmanager
async def lifespan(_app):
    init_db()
    yield


app = FastAPI(title='HospitalOps', docs_url=None, redoc_url=None, lifespan=lifespan)
app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get('SESSION_SECRET', 'SOLO-DESARROLLO-CAMBIA-ESTA-CLAVE'),
    session_cookie='hospitalops_session',
    same_site='lax',
    https_only=os.environ.get('SESSION_HTTPS_ONLY', 'false').lower() == 'true',
    max_age=60 * 60 * 10,
)
app.mount('/static', StaticFiles(directory=os.path.join(BASE, 'static')), name='static')
templates = Jinja2Templates(directory=os.path.join(BASE, 'templates'))

ROLES = {
    'superadmin': 'Administrador de plataforma',
    'admin_cliente': 'Administrador hospital',
    'coordinador': 'Coordinador',
    'tecnico': 'Técnico',
    'solicitante': 'Solicitante',
}
ADMINS = {'superadmin', 'admin_cliente'}
MANAGERS = {'superadmin', 'admin_cliente', 'coordinador'}
STAFF = MANAGERS | {'tecnico'}
PRIORITIES = ['baja', 'media', 'alta', 'critica']
TICKET_STATUSES = ['pendiente', 'abierto', 'en_proceso', 'resuelto', 'cerrado', 'rechazado']
STAGES = ['nuevo', 'contactado', 'propuesta', 'negociacion', 'ganado', 'perdido']


def redirect(path='/dashboard'):
    return RedirectResponse(path, status_code=303)


def flash(request: Request, message: str, level: str = 'success'):
    request.session['flash'] = {'message': message, 'level': level}


def csrf(request: Request):
    if 'csrf' not in request.session:
        request.session['csrf'] = secrets.token_urlsafe(30)
    return request.session['csrf']


async def form_data(request: Request) -> Any:
    data = await request.form()
    if data.get('_csrf', '') != request.session.get('csrf') or not data.get('_csrf'):
        raise HTTPException(status_code=403, detail='Token CSRF inválido. Recarga la página.')
    return data


def clean(data: Any, key: str, maxlen: int = 250, default: str = '') -> str:
    return str(data.get(key, default) or '').strip()[:maxlen]


def positive_int(data, key, default=0) -> int:
    try:
        result = int(data.get(key, default))
    except (ValueError, TypeError):
        raise HTTPException(400, f'Número inválido: {key}')
    if result < 0 or result > 2_147_483_647:
        raise HTTPException(400, f'El valor {key} está fuera de rango')
    return result


def money(data, key, default='0') -> Decimal:
    try:
        value = Decimal(str(data.get(key, default))).quantize(Decimal('0.01'))
        if not value.is_finite() or value < 0 or value > 999_999_999_999:
            raise ValueError()
        return value
    except (InvalidOperation, ValueError):
        raise HTTPException(400, f'Monto inválido: {key}')


def chosen_id(data, key):
    raw = clean(data, key, 25)
    if not raw:
        return None
    try:
        number = int(raw)
        if number <= 0:
            raise ValueError()
        return number
    except ValueError:
        raise HTTPException(400, f'Identificador inválido: {key}')


def actor(request: Request, db: Session) -> User:
    user_id = request.session.get('uid')
    if not user_id:
        raise HTTPException(401, 'Debes iniciar sesión')
    user = db.get(User, user_id)
    if not user or not user.active:
        request.session.clear()
        raise HTTPException(401, 'Cuenta desactivada o sesión expirada')
    if user.approval != 'approved':
        raise HTTPException(403, 'Tu cuenta aún no está aprobada')
    if user.hospital_id and (not user.hospital or not user.hospital.active):
        request.session.clear()
        raise HTTPException(403, 'Hospital desactivado')
    return user


def hospital_for(request: Request, db: Session, user: User) -> Hospital:
    if user.role != 'superadmin':
        if not user.hospital_id:
            raise HTTPException(403, 'Usuario sin hospital')
        return user.hospital
    desired = request.session.get('hospital_id')
    hospital = db.get(Hospital, desired) if desired else None
    if not hospital or not hospital.active:
        hospital = db.scalar(select(Hospital).where(Hospital.active.is_(True)).order_by(Hospital.id))
    if not hospital:
        raise HTTPException(409, 'Primero registra un hospital desde Clientes')
    return hospital


def require(request: Request, db: Session, roles=None, module=None, allow_no_hospital=False):
    user = actor(request, db)
    if roles and user.role not in roles:
        raise HTTPException(403, 'No tienes permisos para esta operación')
    hospital = None
    if not allow_no_hospital:
        hospital = hospital_for(request, db, user)
        if module and not getattr(hospital, f'{module}_enabled'):
            raise HTTPException(403, 'Módulo desactivado en este hospital')
    return user, hospital


def scoped(db: Session, model, entity_id: int, hospital: Hospital):
    found = db.scalar(select(model).where(model.id == entity_id, model.hospital_id == hospital.id))
    if not found:
        raise HTTPException(404, 'Registro inexistente en este hospital')
    return found


def template(request: Request, db: Session, file: str, **context):
    user_id = request.session.get('uid')
    user = db.get(User, user_id) if user_id else None
    hospital = None
    if user and user.active and user.approval == 'approved':
        try:
            hospital = hospital_for(request, db, user)
        except HTTPException:
            pass
    hospitals = db.scalars(select(Hospital).order_by(Hospital.name)).all() if user and user.role == 'superadmin' else []
    payload = {
        'request': request, 'user': user, 'hospital': hospital,
        'hospitals': hospitals, 'csrf_token': csrf(request),
        'flash': request.session.pop('flash', None), 'roles': ROLES,
        'is_admin': bool(user and user.role in ADMINS),
        'is_manager': bool(user and user.role in MANAGERS),
        'is_staff': bool(user and user.role in STAFF),
        'stages': STAGES, 'priorities': PRIORITIES, 'ticket_statuses': TICKET_STATUSES,
    }
    payload.update(context)
    return templates.TemplateResponse(request, file, payload)


def log(db: Session, user: User, hospital_id, action, entity, entity_id, detail=''):
    db.add(AuditLog(hospital_id=hospital_id, actor_id=user.id, action=action,
                    entity=entity, entity_id=entity_id, detail=detail[:250]))


def safe_flush(db: Session, message='El registro ya existe'):
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, message)


def unique_commit(db: Session, message='El registro ya existe'):
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, message)


def ensure_hospital_user(db, user_id, hospital, allowed_roles=None, required=False):
    if user_id is None:
        if required:
            raise HTTPException(400, 'Debes seleccionar un usuario')
        return None
    user = db.scalar(select(User).where(User.id == user_id, User.hospital_id == hospital.id,
                                        User.active.is_(True), User.approval == 'approved'))
    if not user or (allowed_roles and user.role not in allowed_roles):
        raise HTTPException(400, 'Usuario inválido para este hospital')
    return user


@app.exception_handler(HTTPException)
async def http_error(request: Request, exc: HTTPException):
    if exc.status_code == 401:
        return redirect('/login')
    with SessionLocal() as db:
        response = template(request, db, 'error.html', code=exc.status_code, detail=exc.detail)
        response.status_code = exc.status_code
        return response


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    with SessionLocal() as db:
        response = template(request, db, 'error.html', code=422, detail='Datos de formulario inválidos')
        response.status_code = 422
        return response


@app.get('/', include_in_schema=False)
def home(request: Request):
    return redirect('/dashboard' if request.session.get('uid') else '/login')


@app.get('/health', include_in_schema=False)
def health():
    return {'status': 'ok'}


@app.get('/login', response_class=HTMLResponse)
def login_screen(request: Request, db: Session = Depends(get_db)):
    if request.session.get('uid'):
        account = db.get(User, request.session.get('uid'))
        return redirect('/dashboard' if account and account.approval == 'approved' else '/pending')
    return template(request, db, 'login.html')


@app.post('/login')
async def login(request: Request, db: Session = Depends(get_db)):
    data = await form_data(request)
    email = clean(data, 'email', 160).lower()
    user = db.scalar(select(User).where(User.email == email))
    if not user or not verify_password(clean(data, 'password', 500), user.password_hash):
        flash(request, 'Correo o contraseña incorrectos', 'error')
        return redirect('/login')
    if not user.active:
        flash(request, 'Cuenta desactivada; contacta al administrador', 'error')
        return redirect('/login')
    if user.hospital_id and (not user.hospital or not user.hospital.active):
        flash(request, 'Hospital desactivado', 'error')
        return redirect('/login')
    request.session.clear()  # regeneración lógica de sesión para no conservar datos anteriores
    request.session['uid'] = user.id
    csrf(request)
    return redirect('/pending' if user.approval != 'approved' else '/dashboard')


@app.post('/logout')
async def logout(request: Request):
    await form_data(request)
    request.session.clear()
    return redirect('/login')


@app.get('/register', response_class=HTMLResponse)
def register_screen(request: Request, db: Session = Depends(get_db)):
    hospitals = db.scalars(select(Hospital).where(Hospital.active.is_(True)).order_by(Hospital.name)).all()
    return template(request, db, 'register.html', public_hospitals=hospitals)


@app.post('/register')
async def register(request: Request, db: Session = Depends(get_db)):
    data = await form_data(request)
    email = clean(data, 'email', 160).lower()
    name = clean(data, 'name', 150)
    password = clean(data, 'password', 500)
    hospital_id = chosen_id(data, 'hospital_id')
    hospital = db.scalar(select(Hospital).where(Hospital.id == hospital_id, Hospital.active.is_(True)))
    if not name or not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email) or len(password) < 10 or not hospital:
        flash(request, 'Completa el nombre, correo, hospital y contraseña (mínimo 10 caracteres)', 'error')
        return redirect('/register')
    user = User(name=name, email=email, password_hash=hash_password(password),
                hospital_id=hospital.id, role='solicitante', approval='pending',
                job_title=clean(data, 'job_title', 120))
    db.add(user)
    unique_commit(db, 'El correo ya está registrado')
    request.session.clear()
    request.session['uid'] = user.id
    csrf(request)
    flash(request, 'Solicitud enviada; un administrador debe aprobar tu acceso')
    return redirect('/pending')


@app.get('/pending', response_class=HTMLResponse)
def pending(request: Request, db: Session = Depends(get_db)):
    user = db.get(User, request.session.get('uid')) if request.session.get('uid') else None
    if not user:
        return redirect('/login')
    if user.approval == 'approved':
        return redirect('/dashboard')
    return template(request, db, 'pending.html', pending_user=user)


@app.post('/switch-hospital')
async def switch_hospital(request: Request, db: Session = Depends(get_db)):
    user, _ = require(request, db, {'superadmin'}, allow_no_hospital=True)
    data = await form_data(request)
    hospital_id = chosen_id(data, 'hospital_id')
    hospital = db.scalar(select(Hospital).where(Hospital.id == hospital_id, Hospital.active.is_(True)))
    if not hospital:
        raise HTTPException(400, 'Hospital no disponible')
    request.session['hospital_id'] = hospital.id
    return redirect('/dashboard')


@app.get('/dashboard', response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    user, hospital = require(request, db)
    query = select(Ticket).where(Ticket.hospital_id == hospital.id)
    if user.role == 'solicitante':
        query = query.where(Ticket.requester_id == user.id)
    if user.role == 'tecnico':
        query = query.where(or_(Ticket.assignee_id == user.id, Ticket.requester_id == user.id))
    tickets = db.scalars(query.order_by(Ticket.created_at.desc()).limit(6)).all()
    events = db.scalars(select(AuditLog).where(AuditLog.hospital_id == hospital.id)
                        .order_by(AuditLog.created_at.desc()).limit(7)).all() if user.role in ADMINS else []
    return template(request, db, 'dashboard.html', tickets=tickets, events=events)


@app.get('/api/dashboard')
def api_dashboard(request: Request, db: Session = Depends(get_db)):
    user, hospital = require(request, db)
    ticket_where = [Ticket.hospital_id == hospital.id]
    if user.role == 'solicitante':
        ticket_where.append(Ticket.requester_id == user.id)
    if user.role == 'tecnico':
        ticket_where.append(or_(Ticket.assignee_id == user.id, Ticket.requester_id == user.id))
    tickets = db.scalars(select(Ticket).where(*ticket_where)).all()
    response = {
        'tickets_total': len(tickets),
        'tickets_active': sum(t.status in ('pendiente', 'abierto', 'en_proceso') for t in tickets),
        'tickets_pending': sum(t.status == 'pendiente' for t in tickets),
        'tickets_resolved': sum(t.status in ('resuelto', 'cerrado') for t in tickets),
    }
    if user.role in STAFF:
        items = db.scalars(select(InventoryItem).where(InventoryItem.hospital_id == hospital.id,
                                                      InventoryItem.active.is_(True))).all()
        response['stock_low'] = sum(i.stock <= i.min_stock for i in items)
        response['stock_value'] = round(sum(float(i.gross_cost) * i.stock for i in items))
    return JSONResponse(response, headers={'Cache-Control': 'no-store'})


# --- HOSPITALES (administrador de plataforma) ---
@app.get('/hospitals', response_class=HTMLResponse)
def hospitals_list(request: Request, db: Session = Depends(get_db)):
    require(request, db, {'superadmin'}, allow_no_hospital=True)
    items = db.scalars(select(Hospital).order_by(Hospital.name)).all()
    return template(request, db, 'hospitals.html', items=items)


@app.get('/hospitals/new', response_class=HTMLResponse)
def hospital_new(request: Request, db: Session = Depends(get_db)):
    require(request, db, {'superadmin'}, allow_no_hospital=True)
    return template(request, db, 'hospital_form.html', item=None)


@app.get('/hospitals/{id}/edit', response_class=HTMLResponse)
def hospital_edit(id: int, request: Request, db: Session = Depends(get_db)):
    require(request, db, {'superadmin'}, allow_no_hospital=True)
    item = db.get(Hospital, id)
    if not item:
        raise HTTPException(404, 'Hospital inexistente')
    return template(request, db, 'hospital_form.html', item=item)


def update_hospital(item, data):
    item.name = clean(data, 'name', 160)
    item.code = clean(data, 'code', 30).upper()
    item.tax_id = clean(data, 'tax_id', 40)
    item.address = clean(data, 'address', 250)
    item.email = clean(data, 'email', 160)
    item.phone = clean(data, 'phone', 50)
    if not item.name or not item.code:
        raise HTTPException(400, 'Nombre y código son obligatorios')


@app.post('/hospitals/new')
async def hospital_create(request: Request, db: Session = Depends(get_db)):
    user, _ = require(request, db, {'superadmin'}, allow_no_hospital=True)
    data = await form_data(request)
    item = Hospital()
    update_hospital(item, data)
    db.add(item)
    safe_flush(db, 'Hospital duplicado')
    log(db, user, item.id, 'crear', 'hospital', item.id, item.name)
    unique_commit(db, 'Ya existe un hospital con ese nombre o código')
    flash(request, 'Hospital creado')
    return redirect('/hospitals')


@app.post('/hospitals/{id}/edit')
async def hospital_update(id: int, request: Request, db: Session = Depends(get_db)):
    user, _ = require(request, db, {'superadmin'}, allow_no_hospital=True)
    item = db.get(Hospital, id)
    if not item:
        raise HTTPException(404)
    data = await form_data(request)
    update_hospital(item, data)
    log(db, user, id, 'editar', 'hospital', id, item.name)
    unique_commit(db, 'Nombre o código duplicado')
    flash(request, 'Hospital actualizado')
    return redirect('/hospitals')


@app.post('/hospitals/{id}/toggle')
async def hospital_toggle(id: int, request: Request, db: Session = Depends(get_db)):
    user, _ = require(request, db, {'superadmin'}, allow_no_hospital=True)
    await form_data(request)
    item = db.get(Hospital, id)
    if not item:
        raise HTTPException(404)
    item.active = not item.active
    log(db, user, id, 'activar' if item.active else 'desactivar', 'hospital', id, item.name)
    db.commit()
    flash(request, 'Estado del hospital actualizado')
    return redirect('/hospitals')


# --- USUARIOS / APROBACIÓN ---
@app.get('/users', response_class=HTMLResponse)
def users_list(request: Request, db: Session = Depends(get_db)):
    user, hospital = require(request, db, ADMINS)
    users = db.scalars(select(User).where(User.hospital_id == hospital.id).order_by(User.name)).all()
    return template(request, db, 'users.html', items=users)


@app.get('/users/new', response_class=HTMLResponse)
def users_new(request: Request, db: Session = Depends(get_db)):
    user, hospital = require(request, db, ADMINS)
    deps = db.scalars(select(Department).where(Department.hospital_id == hospital.id)).all()
    return template(request, db, 'user_form.html', item=None, deps=deps)


@app.get('/users/{id}/edit', response_class=HTMLResponse)
def user_edit(id: int, request: Request, db: Session = Depends(get_db)):
    user, hospital = require(request, db, ADMINS)
    item = scoped(db, User, id, hospital)
    deps = db.scalars(select(Department).where(Department.hospital_id == hospital.id)).all()
    return template(request, db, 'user_form.html', item=item, deps=deps)


def update_user(item, data, hospital, db, current, is_new=False):
    role = clean(data, 'role', 25)
    if role not in ROLES or role == 'superadmin':
        raise HTTPException(400, 'Rol no permitido')
    if item.id == current.id and role != current.role:
        raise HTTPException(403, 'No puedes cambiar tu propio rol')
    item.name = clean(data, 'name', 150)
    item.email = clean(data, 'email', 160).lower()
    item.job_title = clean(data, 'job_title', 120)
    item.role = role
    item.hospital_id = hospital.id
    dep_id = chosen_id(data, 'department_id')
    if dep_id and not db.scalar(select(Department).where(Department.id == dep_id,
                                                        Department.hospital_id == hospital.id)):
        raise HTTPException(400, 'Área inválida')
    item.department_id = dep_id
    password = clean(data, 'password', 500)
    if is_new and len(password) < 10:
        raise HTTPException(400, 'La contraseña debe tener al menos 10 caracteres')
    if password:
        if len(password) < 10:
            raise HTTPException(400, 'La contraseña debe tener al menos 10 caracteres')
        item.password_hash = hash_password(password)
    if not item.name or not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', item.email):
        raise HTTPException(400, 'Nombre y correo válido son obligatorios')
    item.approval = 'approved'


@app.post('/users/new')
async def users_create(request: Request, db: Session = Depends(get_db)):
    user, hospital = require(request, db, ADMINS)
    data = await form_data(request)
    item = User()
    update_user(item, data, hospital, db, user, True)
    db.add(item)
    safe_flush(db, 'Correo ya registrado')
    log(db, user, hospital.id, 'crear', 'usuario', item.id, item.name)
    unique_commit(db, 'El correo ya está registrado')
    flash(request, 'Usuario creado')
    return redirect('/users')


@app.post('/users/{id}/edit')
async def users_update(id: int, request: Request, db: Session = Depends(get_db)):
    user, hospital = require(request, db, ADMINS)
    item = scoped(db, User, id, hospital)
    data = await form_data(request)
    update_user(item, data, hospital, db, user)
    log(db, user, hospital.id, 'editar', 'usuario', item.id, item.name)
    unique_commit(db, 'El correo ya está registrado')
    flash(request, 'Usuario actualizado')
    return redirect('/users')


@app.post('/users/{id}/toggle')
async def users_toggle(id: int, request: Request, db: Session = Depends(get_db)):
    user, hospital = require(request, db, ADMINS)
    await form_data(request)
    item = scoped(db, User, id, hospital)
    if item.id == user.id:
        raise HTTPException(403, 'No puedes desactivar tu propia cuenta')
    item.active = not item.active
    log(db, user, hospital.id, 'activar' if item.active else 'desactivar', 'usuario', id, item.name)
    db.commit()
    flash(request, 'Estado de usuario actualizado')
    return redirect('/users')


@app.get('/approvals', response_class=HTMLResponse)
def approvals(request: Request, db: Session = Depends(get_db)):
    user, hospital = require(request, db, ADMINS)
    items = db.scalars(select(User).where(User.hospital_id == hospital.id,
                                           User.approval == 'pending').order_by(User.created_at)).all()
    return template(request, db, 'approvals.html', items=items)


@app.post('/approvals/{id}/{action}')
async def approval_decision(id: int, action: str, request: Request, db: Session = Depends(get_db)):
    user, hospital = require(request, db, ADMINS)
    await form_data(request)
    if action not in ('approve', 'reject'):
        raise HTTPException(400)
    item = scoped(db, User, id, hospital)
    if item.approval != 'pending':
        raise HTTPException(409, 'Solicitud ya procesada')
    item.approval = 'approved' if action == 'approve' else 'rejected'
    log(db, user, hospital.id, action, 'usuario', id, item.email)
    db.commit()
    flash(request, 'Solicitud procesada')
    return redirect('/approvals')


@app.get('/departments', response_class=HTMLResponse)
def departments(request: Request, db: Session = Depends(get_db)):
    user, hospital = require(request, db, ADMINS)
    items = db.scalars(select(Department).where(Department.hospital_id == hospital.id).order_by(Department.name)).all()
    return template(request, db, 'departments.html', items=items)


@app.post('/departments')
async def departments_create(request: Request, db: Session = Depends(get_db)):
    user, hospital = require(request, db, ADMINS)
    data = await form_data(request)
    name = clean(data, 'name', 120)
    if not name:
        raise HTTPException(400, 'El área no puede estar vacía')
    item = Department(hospital_id=hospital.id, name=name)
    db.add(item)
    safe_flush(db, 'Área duplicada')
    log(db, user, hospital.id, 'crear', 'area', item.id, item.name)
    unique_commit(db, 'Ya existe un área con ese nombre')
    flash(request, 'Área creada')
    return redirect('/departments')


# --- EQUIPOS / ACTIVOS ---
@app.get('/assets', response_class=HTMLResponse)
def assets(request: Request, db: Session = Depends(get_db)):
    user, hospital = require(request, db, STAFF, 'inventory')
    items = db.scalars(select(Asset).where(Asset.hospital_id == hospital.id).order_by(Asset.name)).all()
    return template(request, db, 'assets.html', items=items)


@app.get('/assets/new', response_class=HTMLResponse)
def assets_new(request: Request, db: Session = Depends(get_db)):
    user, hospital = require(request, db, MANAGERS, 'inventory')
    return template(request, db, 'asset_form.html', item=None)


@app.get('/assets/{id}/edit', response_class=HTMLResponse)
def assets_edit(id: int, request: Request, db: Session = Depends(get_db)):
    user, hospital = require(request, db, MANAGERS, 'inventory')
    return template(request, db, 'asset_form.html', item=scoped(db, Asset, id, hospital))


@app.post('/assets/{id}/save')
@app.post('/assets/new')
async def assets_save(request: Request, id: int | None = None, db: Session = Depends(get_db)):
    user, hospital = require(request, db, MANAGERS, 'inventory')
    data = await form_data(request)
    item = scoped(db, Asset, id, hospital) if id is not None else Asset(hospital_id=hospital.id)
    item.code = clean(data, 'code', 70).upper()
    item.name = clean(data, 'name', 150)
    item.category = clean(data, 'category', 90)
    item.serial_number = clean(data, 'serial_number', 100)
    item.location = clean(data, 'location', 150)
    item.active = data.get('active') == 'on'
    if not item.code or not item.name:
        raise HTTPException(400, 'Código y nombre obligatorios')
    db.add(item)
    safe_flush(db, 'Código de activo duplicado')
    log(db, user, hospital.id, 'editar' if id else 'crear', 'activo', item.id, item.code)
    unique_commit(db, 'El código del activo ya existe')
    flash(request, 'Equipo registrado')
    return redirect('/assets')

# --- TICKETS ---
def ticket_visible(user, ticket):
    if user.role == 'solicitante' and ticket.requester_id != user.id:
        raise HTTPException(404, 'Ticket no encontrado')
    if user.role == 'tecnico' and ticket.assignee_id != user.id and ticket.requester_id != user.id:
        raise HTTPException(404, 'Ticket no asignado a tu cuenta')


@app.get('/tickets', response_class=HTMLResponse)
def tickets(request: Request, db: Session = Depends(get_db)):
    user, hospital = require(request, db, module='tickets')
    query = select(Ticket).where(Ticket.hospital_id == hospital.id)
    if user.role == 'solicitante':
        query = query.where(Ticket.requester_id == user.id)
    if user.role == 'tecnico':
        query = query.where(or_(Ticket.assignee_id == user.id, Ticket.requester_id == user.id))
    status = request.query_params.get('status', '')
    q = request.query_params.get('q', '').strip()[:100]
    if status in TICKET_STATUSES:
        query = query.where(Ticket.status == status)
    if q:
        query = query.where(or_(Ticket.title.ilike(f'%{q}%'), Ticket.description.ilike(f'%{q}%')))
    items = db.scalars(query.order_by(Ticket.created_at.desc()).limit(250)).all()
    return template(request, db, 'tickets.html', items=items, status=status, q=q)


@app.get('/tickets/new', response_class=HTMLResponse)
def ticket_new(request: Request, db: Session = Depends(get_db)):
    user, hospital = require(request, db, module='tickets')
    assets = db.scalars(select(Asset).where(Asset.hospital_id == hospital.id, Asset.active.is_(True))).all()
    return template(request, db, 'ticket_form.html', assets=assets)


@app.post('/tickets/new')
async def ticket_create(request: Request, db: Session = Depends(get_db)):
    user, hospital = require(request, db, module='tickets')
    data = await form_data(request)
    title, description = clean(data, 'title', 200), clean(data, 'description', 5000)
    if not title or not description:
        raise HTTPException(400, 'Título y descripción son obligatorios')
    asset_id = chosen_id(data, 'asset_id')
    if asset_id:
        scoped(db, Asset, asset_id, hospital)
    priority = clean(data, 'priority', 20)
    if priority not in PRIORITIES:
        raise HTTPException(400, 'Prioridad inválida')
    item = Ticket(hospital_id=hospital.id, requester_id=user.id, title=title,
                  description=description, category=clean(data, 'category', 90) or 'Soporte',
                  priority=priority, location=clean(data, 'location', 150), asset_id=asset_id,
                  status='pendiente')
    db.add(item)
    db.flush()
    log(db, user, hospital.id, 'crear', 'ticket', item.id, title)
    db.commit()
    flash(request, f'Ticket #{item.id} enviado. Pendiente de confirmación administrativa')
    return redirect(f'/tickets/{item.id}')


@app.get('/tickets/{id}', response_class=HTMLResponse)
def ticket_detail(id: int, request: Request, db: Session = Depends(get_db)):
    user, hospital = require(request, db, module='tickets')
    item = scoped(db, Ticket, id, hospital)
    ticket_visible(user, item)
    query = select(TicketComment).where(TicketComment.ticket_id == id)
    if user.role == 'solicitante':
        query = query.where(TicketComment.internal.is_(False))
    comments = db.scalars(query.order_by(TicketComment.created_at)).all()
    assignees = db.scalars(select(User).where(User.hospital_id == hospital.id,
                                               User.role.in_(['coordinador', 'tecnico']),
                                               User.active.is_(True), User.approval == 'approved').order_by(User.name)).all() if user.role in MANAGERS else []
    return template(request, db, 'ticket_detail.html', item=item, comments=comments, assignees=assignees)


@app.post('/tickets/{id}/confirm')
async def ticket_confirm(id: int, request: Request, db: Session = Depends(get_db)):
    user, hospital = require(request, db, ADMINS, 'tickets')
    await form_data(request)
    item = scoped(db, Ticket, id, hospital)
    if item.status != 'pendiente':
        raise HTTPException(409, 'El ticket ya fue confirmado o rechazado')
    item.status = 'abierto'
    item.confirmed_by_id = user.id
    item.confirmed_at = now()
    log(db, user, hospital.id, 'confirmar', 'ticket', id, item.title)
    db.commit()
    flash(request, 'Ticket confirmado, listo para asignar')
    return redirect(f'/tickets/{id}')


@app.post('/tickets/{id}/reject')
async def ticket_reject(id: int, request: Request, db: Session = Depends(get_db)):
    user, hospital = require(request, db, ADMINS, 'tickets')
    await form_data(request)
    item = scoped(db, Ticket, id, hospital)
    if item.status != 'pendiente':
        raise HTTPException(409, 'Solo se rechazan tickets pendientes')
    item.status = 'rechazado'
    log(db, user, hospital.id, 'rechazar', 'ticket', id, item.title)
    db.commit()
    flash(request, 'Ticket rechazado')
    return redirect(f'/tickets/{id}')


@app.post('/tickets/{id}/assign')
async def ticket_assign(id: int, request: Request, db: Session = Depends(get_db)):
    user, hospital = require(request, db, MANAGERS, 'tickets')
    data = await form_data(request)
    item = scoped(db, Ticket, id, hospital)
    if item.status in ('pendiente', 'rechazado', 'cerrado'):
        raise HTTPException(409, 'Confirma el ticket antes de asignar')
    user_id = chosen_id(data, 'assignee_id')
    ensure_hospital_user(db, user_id, hospital, {'tecnico', 'coordinador'})
    item.assignee_id = user_id
    log(db, user, hospital.id, 'asignar', 'ticket', id, f'Responsable: {user_id}')
    db.commit()
    flash(request, 'Responsable actualizado')
    return redirect(f'/tickets/{id}')


@app.post('/tickets/{id}/status')
async def ticket_update_status(id: int, request: Request, db: Session = Depends(get_db)):
    user, hospital = require(request, db, STAFF, 'tickets')
    data = await form_data(request)
    item = scoped(db, Ticket, id, hospital)
    ticket_visible(user, item)
    new_status = clean(data, 'status', 25)
    allowed = {
        'abierto': {'en_proceso', 'resuelto'},
        'en_proceso': {'abierto', 'resuelto'},
        'resuelto': {'en_proceso', 'cerrado'},
        'cerrado': {'abierto'} if user.role in ADMINS else set(),
    }
    if new_status not in allowed.get(item.status, set()):
        raise HTTPException(400, 'Transición de estado no permitida')
    if user.role == 'tecnico' and (item.assignee_id != user.id or new_status not in ('en_proceso', 'resuelto', 'abierto')):
        raise HTTPException(403)
    item.status = new_status
    log(db, user, hospital.id, 'estado', 'ticket', id, new_status)
    db.commit()
    flash(request, 'Estado actualizado')
    return redirect(f'/tickets/{id}')


@app.post('/tickets/{id}/close')
async def ticket_requester_close(id: int, request: Request, db: Session = Depends(get_db)):
    user, hospital = require(request, db, module='tickets')
    await form_data(request)
    item = scoped(db, Ticket, id, hospital)
    if user.role != 'solicitante' or item.requester_id != user.id or item.status != 'resuelto':
        raise HTTPException(403, 'Solo el solicitante puede aceptar la resolución')
    item.status = 'cerrado'
    log(db, user, hospital.id, 'aceptar_resolucion', 'ticket', id, item.title)
    db.commit()
    flash(request, 'Resolución aceptada. Ticket cerrado')
    return redirect(f'/tickets/{id}')


@app.post('/tickets/{id}/comments')
async def ticket_comment(id: int, request: Request, db: Session = Depends(get_db)):
    user, hospital = require(request, db, module='tickets')
    data = await form_data(request)
    item = scoped(db, Ticket, id, hospital)
    ticket_visible(user, item)
    body = clean(data, 'body', 4000)
    if not body:
        raise HTTPException(400, 'El comentario está vacío')
    internal = data.get('internal') == 'on'
    if internal and user.role not in STAFF:
        raise HTTPException(403)
    db.add(TicketComment(ticket_id=id, author_id=user.id, body=body, internal=internal))
    log(db, user, hospital.id, 'comentar', 'ticket', id, 'Nota interna' if internal else 'Comentario')
    db.commit()
    flash(request, 'Comentario publicado')
    return redirect(f'/tickets/{id}#comments')


# --- INVENTARIO / KARDEX ---
@app.get('/inventory', response_class=HTMLResponse)
def inventory(request: Request, db: Session = Depends(get_db)):
    user, hospital = require(request, db, STAFF, 'inventory')
    query = select(InventoryItem).where(InventoryItem.hospital_id == hospital.id)
    q = request.query_params.get('q', '').strip()[:100]
    if q:
        query = query.where(or_(InventoryItem.name.ilike(f'%{q}%'), InventoryItem.sku.ilike(f'%{q}%'),
                                InventoryItem.barcode.ilike(f'%{q}%')))
    items = db.scalars(query.order_by(InventoryItem.name).limit(500)).all()
    return template(request, db, 'inventory.html', items=items, q=q)


@app.get('/inventory/new', response_class=HTMLResponse)
def inventory_new(request: Request, db: Session = Depends(get_db)):
    require(request, db, MANAGERS, 'inventory')
    return template(request, db, 'inventory_form.html', item=None)


@app.get('/inventory/{id}/edit', response_class=HTMLResponse)
def inventory_edit(id: int, request: Request, db: Session = Depends(get_db)):
    user, hospital = require(request, db, MANAGERS, 'inventory')
    return template(request, db, 'inventory_form.html', item=scoped(db, InventoryItem, id, hospital))


@app.post('/inventory/new')
@app.post('/inventory/{id}/edit')
async def inventory_save(request: Request, id: int | None = None, db: Session = Depends(get_db)):
    user, hospital = require(request, db, MANAGERS, 'inventory')
    data = await form_data(request)
    item = scoped(db, InventoryItem, id, hospital) if id is not None else InventoryItem(hospital_id=hospital.id)
    item.name = clean(data, 'name', 160)
    item.sku = clean(data, 'sku', 60).upper()
    item.barcode = clean(data, 'barcode', 100)
    item.category = clean(data, 'category', 100)
    item.location = clean(data, 'location', 150)
    item.gross_cost = money(data, 'gross_cost')
    item.sale_price = money(data, 'sale_price')
    item.min_stock = positive_int(data, 'min_stock')
    item.active = data.get('active') == 'on'
    if not item.name or not item.sku:
        raise HTTPException(400, 'SKU y nombre son obligatorios')
    if id is None:
        item.stock = positive_int(data, 'stock')
        db.add(item)
        safe_flush(db, 'SKU ya registrado')
        if item.stock:
            db.add(InventoryMovement(hospital_id=hospital.id, item_id=item.id, actor_id=user.id,
                                     kind='inicial', delta=item.stock, resulting_stock=item.stock,
                                     note='Carga inicial'))
    log(db, user, hospital.id, 'editar' if id else 'crear', 'producto', item.id, item.sku)
    unique_commit(db, 'El SKU ya existe en este hospital')
    flash(request, 'Producto guardado. Para modificar stock utiliza Kardex / Movimientos')
    return redirect('/inventory')


@app.get('/inventory/{id}', response_class=HTMLResponse)
def inventory_detail(id: int, request: Request, db: Session = Depends(get_db)):
    user, hospital = require(request, db, STAFF, 'inventory')
    item = scoped(db, InventoryItem, id, hospital)
    moves = db.scalars(select(InventoryMovement).where(InventoryMovement.hospital_id == hospital.id,
                                                        InventoryMovement.item_id == id)
                       .order_by(InventoryMovement.created_at.desc()).limit(100)).all()
    return template(request, db, 'inventory_detail.html', item=item, moves=moves)


@app.post('/inventory/{id}/move')
async def inventory_move(id: int, request: Request, db: Session = Depends(get_db)):
    user, hospital = require(request, db, MANAGERS, 'inventory')
    data = await form_data(request)
    item = db.scalar(select(InventoryItem).where(InventoryItem.id == id, InventoryItem.hospital_id == hospital.id).with_for_update())
    if not item:
        raise HTTPException(404, 'Producto no encontrado en este hospital')
    if not item.active:
        raise HTTPException(409, 'No se mueve stock de artículos inactivos')
    kind = clean(data, 'kind', 25)
    amount = positive_int(data, 'amount')
    if kind not in ('entrada', 'salida', 'ajuste') or (kind != 'ajuste' and amount == 0):
        raise HTTPException(400, 'Movimiento inválido')
    delta = amount if kind == 'entrada' else -amount if kind == 'salida' else amount - item.stock
    if item.stock + delta < 0:
        raise HTTPException(409, 'Stock insuficiente')
    ticket_id = chosen_id(data, 'ticket_id')
    if ticket_id:
        scoped(db, Ticket, ticket_id, hospital)
    note = clean(data, 'note', 250)
    if not note:
        raise HTTPException(400, 'Debes indicar el motivo del movimiento')
    item.stock += delta
    db.add(InventoryMovement(hospital_id=hospital.id, item_id=id, actor_id=user.id,
                             kind=kind, delta=delta, resulting_stock=item.stock, note=note, ticket_id=ticket_id))
    log(db, user, hospital.id, kind, 'producto', id, f'{delta:+d} unidades — {note}')
    db.commit()
    flash(request, f'Stock actualizado: {item.stock} unidades')
    return redirect(f'/inventory/{id}')


@app.get('/inventory/export/csv')
def inventory_export(request: Request, db: Session = Depends(get_db)):
    user, hospital = require(request, db, MANAGERS, 'inventory')
    items = db.scalars(select(InventoryItem).where(InventoryItem.hospital_id == hospital.id)).all()
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(['SKU', 'Código barras', 'Producto', 'Categoría', 'Ubicación',
                     'Precio bruto', 'Precio venta', 'Stock', 'Stock mínimo', 'Activo'])
    def csv_safe(value):
        string = str(value if value is not None else '')
        return "'" + string if string.startswith(('=', '+', '-', '@', '\t', '\r')) else string
    for i in items:
        writer.writerow([csv_safe(field) for field in [i.sku, i.barcode, i.name, i.category,
                        i.location, i.gross_cost, i.sale_price, i.stock, i.min_stock, i.active]])
    return StreamingResponse(iter([out.getvalue().encode('utf-8-sig')]), media_type='text/csv',
                             headers={'Content-Disposition': 'attachment; filename="inventario.csv"'})


@app.get('/counts', response_class=HTMLResponse)
def counts(request: Request, db: Session = Depends(get_db)):
    user, hospital = require(request, db, STAFF, 'inventory')
    items = db.scalars(select(StockCount).where(StockCount.hospital_id == hospital.id)
                       .order_by(StockCount.created_at.desc())).all()
    return template(request, db, 'counts.html', items=items)


@app.post('/counts/new')
async def count_create(request: Request, db: Session = Depends(get_db)):
    user, hospital = require(request, db, MANAGERS, 'inventory')
    data = await form_data(request)
    item = StockCount(hospital_id=hospital.id, created_by_id=user.id, note=clean(data, 'note', 200))
    db.add(item)
    safe_flush(db)
    inventory_items = db.scalars(select(InventoryItem).where(InventoryItem.hospital_id == hospital.id,
                                                             InventoryItem.active.is_(True)).order_by(InventoryItem.name)).all()
    if not inventory_items:
        raise HTTPException(400, 'Primero registra productos activos')
    for inv in inventory_items:
        db.add(StockCountLine(stock_count_id=item.id, item_id=inv.id, expected_stock=inv.stock))
    log(db, user, hospital.id, 'crear', 'conteo', item.id, item.note)
    db.commit()
    flash(request, 'Conteo abierto; registra el stock físico de cada producto')
    return redirect(f'/counts/{item.id}')


@app.get('/counts/{id}', response_class=HTMLResponse)
def count_detail(id: int, request: Request, db: Session = Depends(get_db)):
    user, hospital = require(request, db, STAFF, 'inventory')
    item = scoped(db, StockCount, id, hospital)
    lines = db.scalars(select(StockCountLine).where(StockCountLine.stock_count_id == id)
                       .order_by(StockCountLine.id)).all()
    return template(request, db, 'count_detail.html', item=item, lines=lines)


@app.post('/counts/{id}/close')
async def count_close(id: int, request: Request, db: Session = Depends(get_db)):
    user, hospital = require(request, db, MANAGERS, 'inventory')
    data = await form_data(request)
    item = scoped(db, StockCount, id, hospital)
    if item.status != 'abierto':
        raise HTTPException(409, 'El conteo ya está cerrado')
    lines = db.scalars(select(StockCountLine).where(StockCountLine.stock_count_id == id)).all()
    changes = []
    for line in lines:
        current = db.scalar(select(InventoryItem).where(InventoryItem.id == line.item_id, InventoryItem.hospital_id == hospital.id).with_for_update())
        if not current:
            raise HTTPException(404, 'Producto del conteo inexistente')
        if current.stock != line.expected_stock:
            raise HTTPException(409, f'Stock de {current.sku} cambió desde la apertura; crea un nuevo conteo')
        actual = positive_int(data, f'actual_{line.id}', line.expected_stock)
        changes.append((line, current, actual))
    for line, current, actual in changes:
        line.actual_stock = actual
        delta = actual - current.stock
        if delta:
            current.stock = actual
            db.add(InventoryMovement(hospital_id=hospital.id, item_id=current.id, actor_id=user.id,
                                     kind='conteo', delta=delta, resulting_stock=actual,
                                     note=f'Ajuste inventario físico #{id}'))
    item.status = 'cerrado'
    item.closed_at = now()
    log(db, user, hospital.id, 'cerrar', 'conteo', id, f'{len(lines)} líneas verificadas')
    db.commit()
    flash(request, 'Inventario físico conciliado y cerrado')
    return redirect(f'/counts/{id}')


# --- CRM ---
@app.get('/crm', response_class=HTMLResponse)
def crm(request: Request, db: Session = Depends(get_db)):
    user, hospital = require(request, db, MANAGERS, 'crm')
    opportunities = db.scalars(select(CRMOpportunity).where(CRMOpportunity.hospital_id == hospital.id)
                               .order_by(CRMOpportunity.created_at.desc())).all()
    by_stage = {stage: [o for o in opportunities if o.stage == stage] for stage in STAGES}
    total_value = sum(float(o.value) for o in opportunities if o.stage not in ('perdido',))
    return template(request, db, 'crm.html', by_stage=by_stage, total_value=total_value, count=len(opportunities))


@app.get('/crm/contacts', response_class=HTMLResponse)
def crm_contacts(request: Request, db: Session = Depends(get_db)):
    user, hospital = require(request, db, MANAGERS, 'crm')
    items = db.scalars(select(CRMContact).where(CRMContact.hospital_id == hospital.id)
                       .order_by(CRMContact.name)).all()
    return template(request, db, 'crm_contacts.html', items=items)


@app.get('/crm/contacts/new', response_class=HTMLResponse)
def crm_contact_new(request: Request, db: Session = Depends(get_db)):
    require(request, db, MANAGERS, 'crm')
    return template(request, db, 'crm_contact_form.html', item=None)


@app.get('/crm/contacts/{id}/edit', response_class=HTMLResponse)
def crm_contact_edit(id: int, request: Request, db: Session = Depends(get_db)):
    user, hospital = require(request, db, MANAGERS, 'crm')
    return template(request, db, 'crm_contact_form.html', item=scoped(db, CRMContact, id, hospital))


@app.post('/crm/contacts/new')
@app.post('/crm/contacts/{id}/edit')
async def crm_contact_save(request: Request, id: int | None = None, db: Session = Depends(get_db)):
    user, hospital = require(request, db, MANAGERS, 'crm')
    data = await form_data(request)
    item = scoped(db, CRMContact, id, hospital) if id is not None else CRMContact(hospital_id=hospital.id)
    item.name = clean(data, 'name', 150)
    item.email = clean(data, 'email', 160)
    item.phone = clean(data, 'phone', 50)
    item.job_title = clean(data, 'job_title', 150)
    item.department = clean(data, 'department', 130)
    item.notes = clean(data, 'notes', 3000)
    if not item.name:
        raise HTTPException(400, 'Nombre requerido')
    db.add(item)
    safe_flush(db)
    log(db, user, hospital.id, 'editar' if id else 'crear', 'contacto', item.id, item.name)
    db.commit()
    flash(request, 'Contacto guardado')
    return redirect('/crm/contacts')


@app.get('/crm/opportunities/new', response_class=HTMLResponse)
def opportunity_new(request: Request, db: Session = Depends(get_db)):
    user, hospital = require(request, db, MANAGERS, 'crm')
    contacts = db.scalars(select(CRMContact).where(CRMContact.hospital_id == hospital.id)).all()
    owners = db.scalars(select(User).where(User.hospital_id == hospital.id, User.role.in_(list(MANAGERS - {'superadmin'})),
                                           User.active.is_(True), User.approval == 'approved')).all()
    return template(request, db, 'crm_opportunity_form.html', item=None, contacts=contacts, owners=owners)


@app.get('/crm/opportunities/{id}/edit', response_class=HTMLResponse)
def opportunity_edit(id: int, request: Request, db: Session = Depends(get_db)):
    user, hospital = require(request, db, MANAGERS, 'crm')
    item = scoped(db, CRMOpportunity, id, hospital)
    contacts = db.scalars(select(CRMContact).where(CRMContact.hospital_id == hospital.id)).all()
    owners = db.scalars(select(User).where(User.hospital_id == hospital.id, User.role.in_(list(MANAGERS - {'superadmin'})),
                                           User.active.is_(True), User.approval == 'approved')).all()
    return template(request, db, 'crm_opportunity_form.html', item=item, contacts=contacts, owners=owners)


@app.post('/crm/opportunities/new')
@app.post('/crm/opportunities/{id}/edit')
async def opportunity_save(request: Request, id: int | None = None, db: Session = Depends(get_db)):
    user, hospital = require(request, db, MANAGERS, 'crm')
    data = await form_data(request)
    item = scoped(db, CRMOpportunity, id, hospital) if id is not None else CRMOpportunity(hospital_id=hospital.id)
    item.name = clean(data, 'name', 190)
    item.value = money(data, 'value')
    item.stage = clean(data, 'stage', 30)
    item.expected_close = clean(data, 'expected_close', 12)
    item.notes = clean(data, 'notes', 4000)
    if item.stage not in STAGES or not item.name:
        raise HTTPException(400, 'Nombre o etapa inválidos')
    contact_id = chosen_id(data, 'contact_id')
    if contact_id:
        scoped(db, CRMContact, contact_id, hospital)
    item.contact_id = contact_id
    owner_id = chosen_id(data, 'owner_id')
    if owner_id:
        ensure_hospital_user(db, owner_id, hospital, {'admin_cliente', 'coordinador'})
    item.owner_id = owner_id
    db.add(item)
    safe_flush(db)
    log(db, user, hospital.id, 'editar' if id else 'crear', 'oportunidad', item.id, item.name)
    db.commit()
    flash(request, 'Oportunidad guardada')
    return redirect('/crm')


@app.post('/crm/opportunities/{id}/stage')
async def opportunity_stage(id: int, request: Request, db: Session = Depends(get_db)):
    user, hospital = require(request, db, MANAGERS, 'crm')
    data = await form_data(request)
    item = scoped(db, CRMOpportunity, id, hospital)
    stage = clean(data, 'stage', 30)
    if stage not in STAGES:
        raise HTTPException(400, 'Etapa inválida')
    item.stage = stage
    log(db, user, hospital.id, 'etapa', 'oportunidad', id, stage)
    db.commit()
    flash(request, 'Oportunidad movida')
    return redirect('/crm')


# --- PERSONALIZACIÓN / AUDITORÍA ---
@app.get('/settings', response_class=HTMLResponse)
def settings(request: Request, db: Session = Depends(get_db)):
    user, hospital = require(request, db, ADMINS)
    return template(request, db, 'settings.html')


@app.post('/settings')
async def settings_update(request: Request, db: Session = Depends(get_db)):
    user, hospital = require(request, db, ADMINS)
    data = await form_data(request)
    color = clean(data, 'color', 7)
    if not re.fullmatch(r'#[A-Fa-f0-9]{6}', color):
        raise HTTPException(400, 'Color hexadecimal inválido')
    portal_name = clean(data, 'portal_name', 90)
    if not portal_name:
        raise HTTPException(400, 'Nombre del portal requerido')
    hospital.color = color
    hospital.portal_name = portal_name
    hospital.tickets_enabled = data.get('tickets_enabled') == 'on'
    hospital.inventory_enabled = data.get('inventory_enabled') == 'on'
    hospital.crm_enabled = data.get('crm_enabled') == 'on'
    log(db, user, hospital.id, 'configurar', 'hospital', hospital.id, 'Imagen corporativa y módulos')
    db.commit()
    flash(request, 'Personalización actualizada')
    return redirect('/settings')


@app.get('/audit', response_class=HTMLResponse)
def audit(request: Request, db: Session = Depends(get_db)):
    user, hospital = require(request, db, ADMINS)
    items = db.scalars(select(AuditLog).where(AuditLog.hospital_id == hospital.id)
                       .order_by(AuditLog.created_at.desc()).limit(300)).all()
    return template(request, db, 'audit.html', items=items)


# Database initialization is handled by the FastAPI lifespan context above.
