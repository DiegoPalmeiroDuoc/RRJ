"""Carga demostrativa opcional. Nunca utilizar cuentas demo en producción."""
from decimal import Decimal
from sqlalchemy import select
from app.database import SessionLocal, init_db
from app.models import (Hospital, Department, User, Asset, InventoryItem,
                        InventoryMovement, Ticket, TicketComment, CRMContact, CRMOpportunity, AuditLog, now)
from app.security import hash_password


def seed_data(db):
    if db.scalar(select(User).limit(1)):
        return False
    norte = Hospital(name='Hospital Demo Norte', code='HDN-001', tax_id='76.000.111-1',
                     address='Av. Salud 1250, Santiago', email='contacto@norte.example',
                     phone='+56 2 2000 0000', portal_name='Portal Hospital Norte', color='#2563eb')
    sur = Hospital(name='Hospital Demo Sur', code='HDS-002', tax_id='76.000.222-2',
                   address='Av. Los Robles 390, Temuco', email='contacto@sur.example',
                   phone='+56 45 200 0000', portal_name='Gestión Hospital Sur', color='#7c3aed')
    db.add_all([norte, sur]); db.flush()
    d1 = Department(hospital_id=norte.id, name='Urgencias')
    d2 = Department(hospital_id=norte.id, name='UCI')
    d3 = Department(hospital_id=sur.id, name='Pabellón')
    db.add_all([d1, d2, d3]); db.flush()
    pwd = hash_password('DemoSeguro2026!')
    root = User(name='Admin Plataforma', email='root@hospitalops.example', password_hash=pwd,
                role='superadmin', active=True, approval='approved')
    admin = User(name='Camila Administradora', email='admin@norte.example', password_hash=pwd,
                 role='admin_cliente', hospital_id=norte.id, approval='approved', job_title='Jefa de operaciones')
    coordinator = User(name='Diego Coordinador', email='coordinador@norte.example', password_hash=pwd,
                       role='coordinador', hospital_id=norte.id, approval='approved', job_title='Coordinador técnico')
    tech = User(name='Sofía Técnica', email='tecnico@norte.example', password_hash=pwd,
                role='tecnico', hospital_id=norte.id, approval='approved', job_title='Técnica electromedicina')
    requester = User(name='Matías Solicitante', email='solicitante@norte.example', password_hash=pwd,
                     role='solicitante', hospital_id=norte.id, department_id=d1.id, approval='approved', job_title='Enfermero')
    pending = User(name='Antonia Pendiente', email='pendiente@norte.example', password_hash=pwd,
                   role='solicitante', hospital_id=norte.id, approval='pending', job_title='TENS')
    admin_sur = User(name='Valentina Administradora', email='admin@sur.example', password_hash=pwd,
                     role='admin_cliente', hospital_id=sur.id, approval='approved', job_title='Administradora')
    requester_sur = User(name='Tomás Solicitante', email='solicitante@sur.example', password_hash=pwd,
                         role='solicitante', hospital_id=sur.id, department_id=d3.id, approval='approved')
    db.add_all([root, admin, coordinator, tech, requester, pending, admin_sur, requester_sur]); db.flush()
    asset = Asset(hospital_id=norte.id, code='EQ-MON-001', name='Monitor multiparámetro',
                  category='Electromedicina', location='UCI · Box 3', serial_number='MON-2045')
    asset2 = Asset(hospital_id=norte.id, code='EQ-BOM-002', name='Bomba de infusión',
                   category='Electromedicina', location='Urgencias', serial_number='BOM-9910')
    db.add_all([asset, asset2]); db.flush()
    t1 = Ticket(hospital_id=norte.id, requester_id=requester.id, assignee_id=tech.id,
                confirmed_by_id=admin.id, confirmed_at=now(), title='Monitor UCI presenta error de pantalla',
                description='El monitor multiparámetro del box 3 no permite ver la curva de saturación. Se requiere diagnóstico.',
                category='Electromedicina', priority='alta', status='en_proceso',
                location='UCI · Box 3', asset_id=asset.id)
    t2 = Ticket(hospital_id=norte.id, requester_id=requester.id,
                title='Reposición de insumos en urgencias', description='Se requiere reposición de stock en la unidad.',
                category='Insumos', priority='media', status='pendiente', location='Urgencias')
    t3 = Ticket(hospital_id=norte.id, requester_id=requester.id, assignee_id=tech.id,
                confirmed_by_id=admin.id, confirmed_at=now(), title='Revisión de bomba de infusión',
                description='Equipo con alarma intermitente. Solicito diagnóstico preventivo.',
                category='Mantenimiento', priority='baja', status='resuelto', asset_id=asset2.id)
    t4 = Ticket(hospital_id=sur.id, requester_id=requester_sur.id,
                title='Control de climatización en pabellón', description='Temperatura fuera de rango.',
                status='pendiente', priority='critica', location='Pabellón')
    db.add_all([t1, t2, t3, t4]); db.flush()
    db.add_all([
        TicketComment(ticket_id=t1.id, author_id=tech.id, body='Se inició inspección eléctrica, verificando alimentación y conexiones.'),
        TicketComment(ticket_id=t1.id, author_id=coordinator.id, body='Revisión pendiente de repuesto.', internal=True),
        TicketComment(ticket_id=t3.id, author_id=tech.id, body='Equipo calibrado y verificado. Solicitud resuelta.'),
    ])
    products = [
        InventoryItem(hospital_id=norte.id, sku='INS-GUA-001', barcode='7801000001001', name='Guantes nitrilo caja 100', category='Insumos', location='Bodega central', gross_cost=Decimal('7200'), sale_price=Decimal('9900'), stock=42, min_stock=10),
        InventoryItem(hospital_id=norte.id, sku='REP-SEN-002', barcode='7801000001002', name='Sensor de oxígeno', category='Repuestos', location='Electromedicina', gross_cost=Decimal('24500'), sale_price=Decimal('38500'), stock=3, min_stock=5),
        InventoryItem(hospital_id=norte.id, sku='INS-JER-003', barcode='7801000001003', name='Jeringa desechable 5 ml', category='Insumos', location='Bodega central', gross_cost=Decimal('190'), sale_price=Decimal('350'), stock=270, min_stock=50),
        InventoryItem(hospital_id=sur.id, sku='SUR-GUA-001', barcode='7801000002001', name='Guantes vinilo caja 100', category='Insumos', location='Bodega sur', gross_cost=Decimal('5600'), sale_price=Decimal('7900'), stock=31, min_stock=6),
    ]
    db.add_all(products); db.flush()
    for p in products:
        db.add(InventoryMovement(hospital_id=p.hospital_id, item_id=p.id, actor_id=(admin.id if p.hospital_id == norte.id else admin_sur.id), kind='inicial', delta=p.stock, resulting_stock=p.stock, note='Datos de demostración'))
    contacts = [
        CRMContact(hospital_id=norte.id, name='Valeria Martínez', email='valeria@example.org',
                   phone='+56 9 5555 1111', job_title='Encargada de compras', department='Abastecimiento'),
        CRMContact(hospital_id=norte.id, name='Ignacio Fuentes', email='ignacio@example.org',
                   phone='+56 9 5555 2222', job_title='Coordinador de contratos', department='Adquisiciones'),
        CRMContact(hospital_id=sur.id, name='Elisa Soto', email='elisa@example.org',
                   job_title='Jefa de adquisiciones', department='Administración'),
    ]
    db.add_all(contacts); db.flush()
    db.add_all([
        CRMOpportunity(hospital_id=norte.id, contact_id=contacts[0].id, owner_id=coordinator.id,
                       name='Mantención anual de monitores', value=Decimal('5800000'), stage='propuesta', expected_close='2026-11-15'),
        CRMOpportunity(hospital_id=norte.id, contact_id=contacts[1].id, owner_id=coordinator.id,
                       name='Renovación de sensores', value=Decimal('1240000'), stage='negociacion', expected_close='2026-11-30'),
        CRMOpportunity(hospital_id=norte.id, contact_id=contacts[0].id,
                       name='Evaluación repuestos de bombas', value=Decimal('720000'), stage='contactado'),
        CRMOpportunity(hospital_id=sur.id, contact_id=contacts[2].id,
                       name='Repuestos climatización', value=Decimal('980000'), stage='nuevo'),
    ])
    db.add(AuditLog(hospital_id=norte.id, actor_id=admin.id, action='cargar_demo',
                    entity='sistema', entity_id=None, detail='Instalación de datos iniciales'))
    db.commit()
    return True


if __name__ == '__main__':
    init_db()
    with SessionLocal() as db:
        created = seed_data(db)
    print('Datos demo creados.' if created else 'Base de datos no vacía; se conservan los datos existentes.')
    if created:
        print('Superadmin: root@hospitalops.example | DemoSeguro2026!')
        print('Admin Norte: admin@norte.example | DemoSeguro2026!')
        print('Admin Sur: admin@sur.example | DemoSeguro2026!')
