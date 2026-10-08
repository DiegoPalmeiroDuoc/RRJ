import os
import re
from pathlib import Path
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app import database, main
from app.models import Base, Hospital, InventoryItem, Ticket, User, StockCount
from seed import seed_data


@pytest.fixture()
def sandbox(tmp_path, monkeypatch):
    engine = create_engine(f'sqlite:///{tmp_path / "test.db"}', connect_args={'check_same_thread': False})
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    monkeypatch.setattr(database, 'engine', engine)
    monkeypatch.setattr(database, 'SessionLocal', Session)
    monkeypatch.setattr(main, 'SessionLocal', Session)
    Base.metadata.create_all(engine)
    with Session() as db:
        seed_data(db)
    with TestClient(main.app, follow_redirects=False) as client:
        yield client, Session
    engine.dispose()


def token(html):
    hit = re.search(r'name="_csrf" value="([^"]+)"', html)
    assert hit, 'Missing CSRF field'
    return hit.group(1)


def signin(client, email):
    res = client.get('/login')
    assert res.status_code == 200
    result = client.post('/login', data={'_csrf':token(res.text), 'email':email,
                                        'password':'DemoSeguro2026!'})
    assert result.status_code == 303
    return result


def form_post(client, route, data):
    page = client.get('/dashboard')
    assert page.status_code == 200
    return client.post(route, data={'_csrf':token(page.text), **data})


def test_health_and_dashboard_widgets(sandbox):
    client, _ = sandbox
    assert client.get('/health').json() == {'status':'ok'}
    signin(client, 'admin@norte.example')
    page = client.get('/dashboard')
    assert page.status_code == 200
    assert 'page-skeleton' in page.text
    assert 'data-async-dashboard' in page.text
    response = client.get('/api/dashboard')
    assert response.status_code == 200
    assert response.json()['tickets_total'] == 3
    assert response.json()['stock_low'] == 1


def test_csrf_and_access_control(sandbox):
    client, _ = sandbox
    signin(client, 'solicitante@norte.example')
    assert client.get('/users').status_code == 403
    assert client.get('/inventory').status_code == 403
    assert client.get('/crm').status_code == 403
    assert client.get('/hospitals').status_code == 403
    assert client.post('/tickets/new', data={'title':'Injection without csrf'}).status_code == 403
    assert client.get('/tickets/4').status_code == 404
    assert client.get('/tickets/1').status_code == 200
    assert 'Revisión pendiente de repuesto.' not in client.get('/tickets/1').text
    assert client.get('/api/dashboard').json()['tickets_total'] == 3


def test_cross_tenant_isolation(sandbox):
    client, _ = sandbox
    signin(client, 'admin@norte.example')
    assert client.get('/tickets/4').status_code == 404
    assert client.get('/inventory/4').status_code == 404
    assert client.get('/crm/contacts/3/edit').status_code == 404
    assert client.get('/assets/1/edit').status_code == 200
    move = form_post(client, '/inventory/1/move', {'kind':'entrada','amount':'2',
                                                    'note':'test', 'ticket_id':'4'})
    assert move.status_code == 404
    assert client.get('/inventory/1').status_code == 200


def test_pending_register_approval_flow(sandbox):
    client, Session = sandbox
    # Admin approves demo pending user.
    signin(client, 'admin@norte.example')
    page = client.get('/approvals')
    assert 'Antonia Pendiente' in page.text
    with Session() as db:
        pending = db.scalar(select(User).where(User.email == 'pendiente@norte.example'))
        id = pending.id
    assert form_post(client, f'/approvals/{id}/approve', {}).status_code == 303
    with Session() as db:
        assert db.get(User, id).approval == 'approved'
    client.cookies.clear()
    signin(client, 'pendiente@norte.example')
    assert client.get('/tickets/new').status_code == 200
    # Registration from a different hospital must not allow admin self-selection.
    client.cookies.clear()
    register = client.get('/register')
    result = client.post('/register', data={'_csrf': token(register.text), 'name':'Nueva Cuenta',
        'email':'nueva@example.org', 'password':'ClaveSegura2026!', 'hospital_id':'2',
        'role':'superadmin', 'job_title':'Enfermería'})
    assert result.status_code == 303 and result.headers['location'] == '/pending'
    with Session() as db:
        newbie = db.scalar(select(User).where(User.email == 'nueva@example.org'))
        assert newbie.role == 'solicitante' and newbie.hospital_id == 2
        assert newbie.approval == 'pending'
    assert client.get('/dashboard').status_code == 403


def test_ticket_confirmation_assignment_completion(sandbox):
    client, Session = sandbox
    signin(client, 'solicitante@norte.example')
    result = form_post(client, '/tickets/new', {'title':'La impresora no funciona',
        'description':'Impresora del box de urgencias sin conexión.', 'priority':'alta',
        'category':'TI', 'location':'Box 2'})
    assert result.status_code == 303
    id = int(result.headers['location'].split('/')[-1])
    assert client.get(f'/tickets/{id}').status_code == 200
    assert form_post(client, f'/tickets/{id}/confirm', {}).status_code == 403
    client.cookies.clear()
    signin(client, 'coordinador@norte.example')
    assert form_post(client, f'/tickets/{id}/assign', {'assignee_id':'4'}).status_code == 409
    client.cookies.clear()
    signin(client, 'admin@norte.example')
    assert form_post(client, f'/tickets/{id}/confirm', {}).status_code == 303
    assert form_post(client, f'/tickets/{id}/assign', {'assignee_id':'4'}).status_code == 303
    client.cookies.clear()
    signin(client, 'tecnico@norte.example')
    assert form_post(client, f'/tickets/{id}/status', {'status':'en_proceso'}).status_code == 303
    assert form_post(client, f'/tickets/{id}/status', {'status':'resuelto'}).status_code == 303
    client.cookies.clear()
    signin(client, 'solicitante@norte.example')
    assert form_post(client, f'/tickets/{id}/close', {}).status_code == 303
    with Session() as db:
        ticket = db.get(Ticket, id)
        assert ticket.status == 'cerrado' and ticket.confirmed_by_id is not None


def test_inventory_movement_count_and_csv(sandbox):
    client, Session = sandbox
    signin(client, 'coordinador@norte.example')
    assert form_post(client, '/inventory/1/move', {
        'kind':'salida','amount':'4','note':'Uso por servicio'}).status_code == 303
    with Session() as db:
        assert db.get(InventoryItem, 1).stock == 38
    assert form_post(client, '/inventory/1/move', {'kind':'salida','amount':'9999',
                                                    'note':'No permitido'}).status_code == 409
    export = client.get('/inventory/export/csv')
    assert export.status_code == 200 and 'INS-GUA-001' in export.text
    create = form_post(client, '/counts/new', {'note':'Inventario semestral'})
    assert create.status_code == 303
    count_id = int(create.headers['location'].split('/')[-1])
    count_page = client.get(f'/counts/{count_id}')
    line_matches = re.findall(r'name="actual_(\d+)" value="(\d+)"', count_page.text)
    assert len(line_matches) == 3
    payload = {f'actual_{k}':v for k,v in line_matches}
    k = line_matches[0][0]
    payload[f'actual_{k}'] = '11'
    assert form_post(client, f'/counts/{count_id}/close', payload).status_code == 303
    with Session() as db:
        assert db.get(StockCount, count_id).status == 'cerrado'
    assert form_post(client, f'/counts/{count_id}/close', payload).status_code == 409


def test_crm_role_and_module_toggle(sandbox):
    client, Session = sandbox
    signin(client, 'admin@norte.example')
    result = form_post(client, '/crm/contacts/new', {'name':'Contacto Nuevo', 'email':'nuevo@example.org'})
    assert result.status_code == 303
    settings = form_post(client, '/settings', {'color':'#d94785','portal_name':'Portal Rojo',
                                               'tickets_enabled':'on', 'inventory_enabled':'on'})
    assert settings.status_code == 303
    assert client.get('/crm').status_code == 403
    assert client.get('/crm/contacts').status_code == 403
    assert 'Portal Rojo' in client.get('/dashboard').text
    # Settings for one hospital never modifies another hospital.
    with Session() as db:
        assert db.get(Hospital, 1).crm_enabled is False
        assert db.get(Hospital, 2).crm_enabled is True


def test_admin_cannot_edit_user_from_other_tenant(sandbox):
    client, Session = sandbox
    signin(client, 'admin@norte.example')
    with Session() as db:
        other_id = db.scalar(select(User).where(User.email == 'admin@sur.example')).id
    assert client.get(f'/users/{other_id}/edit').status_code == 404
    assert form_post(client, f'/users/{other_id}/toggle', {}).status_code == 404


def test_all_admin_and_manager_views_render(sandbox):
    client, _ = sandbox
    signin(client, 'admin@norte.example')
    paths = [
        '/dashboard', '/users', '/users/new', '/users/2/edit', '/approvals', '/departments',
        '/tickets', '/tickets/new', '/tickets/1', '/inventory', '/inventory/new',
        '/inventory/1', '/inventory/1/edit', '/counts', '/assets', '/assets/new',
        '/assets/1/edit', '/crm', '/crm/contacts', '/crm/contacts/new',
        '/crm/contacts/1/edit', '/crm/opportunities/new', '/crm/opportunities/1/edit',
        '/settings', '/audit',
    ]
    for path in paths:
        response = client.get(path)
        assert response.status_code == 200, f'{path}: {response.status_code}'
        assert '<!DOCTYPE html>' in response.text
        assert 'csrf' in response.text


def test_superadmin_hospital_management_and_switch(sandbox):
    client, Session = sandbox
    signin(client, 'root@hospitalops.example')
    for path in ['/hospitals', '/hospitals/new', '/hospitals/1/edit']:
        assert client.get(path).status_code == 200
    result = form_post(client, '/hospitals/new', {'name':'Hospital Demo Occidente',
        'code':'HDO-030', 'tax_id':'76.200.000-0', 'address':'Calle Uno', 'email':'hdo@example.org'})
    assert result.status_code == 303
    with Session() as db:
        hospital = db.scalar(select(Hospital).where(Hospital.code == 'HDO-030'))
        assert hospital is not None and hospital.active
        new_id = hospital.id
    assert form_post(client, f'/hospitals/{new_id}/toggle', {}).status_code == 303
    with Session() as db:
        assert not db.get(Hospital, new_id).active
    assert form_post(client, '/switch-hospital', {'hospital_id':'2'}).status_code == 303
    assert 'Hospital Demo Sur' in client.get('/dashboard').text
    assert client.get('/tickets/1').status_code == 404
    assert client.get('/tickets/4').status_code == 200


def test_entity_create_edit_flows(sandbox):
    client, Session = sandbox
    signin(client, 'admin@norte.example')
    assert form_post(client, '/departments', {'name':'Laboratorio'}).status_code == 303
    assert form_post(client, '/users/new', {'name':'Nuevo Tecnico','email':'nt@example.org',
        'role':'tecnico','password':'UnaPassword2026!','job_title':'Soporte'}).status_code == 303
    assert form_post(client, '/assets/new', {'code':'EQ-NUEVO', 'name':'Refrigerador laboratorio',
        'category':'Laboratorio','serial_number':'SN99','location':'Laboratorio','active':'on'}).status_code == 303
    assert form_post(client, '/inventory/new', {'sku':'NUEVO-SKU','name':'Filtro de aire',
        'gross_cost':'13000', 'sale_price':'18000','stock':'4','min_stock':'1',
        'category':'Filtros','location':'Bodega principal','active':'on'}).status_code == 303
    assert form_post(client, '/crm/opportunities/new', {'name':'Licitación anual',
        'value':'58000','stage':'nuevo','contact_id':'1','owner_id':'3'}).status_code == 303
    with Session() as db:
        inv = db.scalar(select(InventoryItem).where(InventoryItem.sku == 'NUEVO-SKU'))
        assert inv.stock == 4 and inv.gross_cost == 13000
    assert form_post(client, f'/inventory/{inv.id}/edit', {
        'sku':'NUEVO-SKU','name':'Filtro de aire XL','gross_cost':'15000','sale_price':'20000',
        'min_stock':'2','category':'Filtros','location':'Bodega','active':'on','stock':'5000',
    }).status_code == 303
    with Session() as db:
        inv = db.get(InventoryItem, inv.id)
        assert inv.stock == 4 and inv.gross_cost == 15000


def test_bootstrap_superadmin_and_no_duplicate(sandbox):
    from create_admin import create_superadmin
    client, Session = sandbox
    with Session() as db:
        user = create_superadmin(db, 'Administración 2', 'admin2@example.org', 'MasSegura2026!')
        assert user.id is not None and user.role == 'superadmin'
        with pytest.raises(ValueError):
            create_superadmin(db, 'Administración 2', 'admin2@example.org', 'MasSegura2026!')
