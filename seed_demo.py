"""Demo extendida: datos ficticios abundantes para presentaciones.

Se ejecuta desde `python seed.py` justo después del seed base (que usan las pruebas automáticas).
Todos los nombres, RUT, correos y teléfonos son inventados. Nunca usar en producción.
"""
from datetime import timedelta
from decimal import Decimal

from sqlalchemy import select

from app.models import (Hospital, Department, User, Asset, Ticket, TicketComment, InventoryItem,
                        InventoryMovement, StockCount, StockCountLine, CRMContact, CRMOpportunity,
                        AuditLog, ProviderItem, TechnicianStock, ProviderMovement, now)
from app.security import hash_password

DEMO_PASSWORD = 'DemoSeguro2026!'
BASE = now()


def ago(days, hours=0):
    return BASE - timedelta(days=days, hours=hours)


def demo_email(name, hospital):
    """'Ana Muñoz' en Hospital Demo Norte -> ana.munoz@norte.example"""
    plain = name.lower().translate(str.maketrans('áéíóúüñ', 'aeiouun'))
    domain = {'HDN-001': 'norte', 'HDS-002': 'sur', 'CDC-003': 'costa'}[hospital.code]
    return f"{'.'.join(plain.split())}@{domain}.example"


def additional_staff(norte, sur, costa):
    """(nombre, cargo, área) — el orden define el rol: 1 coordinador, 2 técnicos, 14 solicitantes, 3 pendientes."""
    return {
        norte: [
            ('Claudia Morales', 'Coordinadora de turno', None),
            ('Ricardo Salinas', 'Técnico en refrigeración', None),
            ('Natalia Opazo', 'Técnica electromedicina', None),
            ('Esteban Carrasco', 'Médico urgenciólogo', 'Urgencias'),
            ('Valentina Saavedra', 'Enfermera', 'Urgencias'),
            ('Diego Venegas', 'TENS', 'Urgencias'),
            ('Macarena Poblete', 'Enfermera', 'UCI'),
            ('Francisco Aguilera', 'Kinesiólogo', 'UCI'),
            ('Bárbara Cifuentes', 'TENS', 'UCI'),
            ('Gonzalo Riquelme', 'Anestesiólogo', 'Pabellón'),
            ('Constanza Lillo', 'Arsenalera', 'Pabellón'),
            ('Felipe Barrientos', 'Pediatra', 'Pediatría'),
            ('Antonia Zúñiga', 'Educadora de párvulos', 'Pediatría'),
            ('Marcela Tapia', 'Tecnóloga médica', 'Imagenología'),
            ('Rodrigo Valdés', 'Tecnólogo médico', 'Laboratorio'),
            ('Pía Henríquez', 'Bioquímica', 'Laboratorio'),
            ('Jorge Sandoval', 'Auxiliar de esterilización', 'Esterilización'),
            ('Sofía Arancibia', 'Enfermera', 'Pediatría'),
            ('Matías Leiva', 'TENS', 'Pabellón'),
            ('Daniela Yáñez', 'Tecnóloga médica', 'Imagenología'),
        ],
        sur: [
            ('Patricio Huenchullán', 'Coordinador de mantenimiento', None),
            ('Alejandra Painemal', 'Técnica electromedicina', None),
            ('Manuel Catrileo', 'Técnico eléctrico', None),
            ('Verónica Manríquez', 'Enfermera', 'Urgencias'),
            ('Cristián Paredes', 'Médico urgenciólogo', 'Urgencias'),
            ('Karina Alarcón', 'TENS', 'Urgencias'),
            ('Luis Quilodrán', 'Cirujano', 'Pabellón'),
            ('Paulina Ancamil', 'Arsenalera', 'Pabellón'),
            ('Eduardo Bustos', 'TENS', 'Pabellón'),
            ('Francisca Llanquileo', 'Enfermera', 'Medicina Interna'),
            ('Mauricio Toledo', 'Médico internista', 'Medicina Interna'),
            ('Javiera Neira', 'Kinesióloga', 'Medicina Interna'),
            ('Héctor Millán', 'Auxiliar de esterilización', 'Esterilización'),
            ('Lorena Cayupán', 'Enfermera', 'Esterilización'),
            ('Ignacio Burgos', 'Tecnólogo médico', 'Imagenología'),
            ('Camila Sáez', 'Radióloga', 'Imagenología'),
            ('Rosa Huaiquil', 'TENS', 'Medicina Interna'),
            ('Andrés Figueroa', 'Enfermero', 'Urgencias'),
            ('Tamara Ñancupil', 'TENS', 'Pabellón'),
            ('Sergio Lagos', 'Tecnólogo médico', 'Imagenología'),
        ],
        costa: [
            ('Carolina Errázuriz', 'Coordinadora de operaciones', None),
            ('Álvaro Mella', 'Técnico electromedicina', None),
            ('Fernanda Olivares', 'Técnica en climatización', None),
            ('Nicolás Bravo', 'Médico urgenciólogo', 'Urgencias'),
            ('Romina Castillo', 'Enfermera', 'Urgencias'),
            ('Vicente Rubio', 'TENS', 'Urgencias'),
            ('Gabriela Montt', 'Cirujana', 'Pabellón'),
            ('Tomás Echeverría', 'Anestesiólogo', 'Pabellón'),
            ('Josefina Larraín', 'Arsenalera', 'Pabellón'),
            ('Amanda Cortés', 'Matrona', 'Maternidad'),
            ('Ignacia Valenzuela', 'Matrona', 'Maternidad'),
            ('Felipe Cáceres', 'Ginecólogo', 'Maternidad'),
            ('Renata Fernández', 'Tecnóloga médica', 'Imagenología'),
            ('Agustín Domínguez', 'Radiólogo', 'Imagenología'),
            ('Elena Rivas', 'Bioquímica', 'Laboratorio'),
            ('Martín Gallardo', 'Tecnólogo médico', 'Laboratorio'),
            ('Catalina Peña', 'TENS', 'Maternidad'),
            ('Bastián Moya', 'Enfermero', 'Urgencias'),
            ('Isabel Soto', 'TENS', 'Pabellón'),
            ('Emilia Carvajal', 'Tecnóloga médica', 'Laboratorio'),
        ],
    }


def seed_demo(db):
    """Agrega la demo extendida sobre el seed base. Devuelve False si ya estaba cargada."""
    if db.scalar(select(Hospital).where(Hospital.code == 'CDC-003')):
        return False
    by_email = lambda email: db.scalar(select(User).where(User.email == email))
    norte = db.scalar(select(Hospital).where(Hospital.code == 'HDN-001'))
    sur = db.scalar(select(Hospital).where(Hospital.code == 'HDS-002'))
    root, admin_norte, coord_norte = by_email('root@hospitalops.example'), by_email('admin@norte.example'), by_email('coordinador@norte.example')
    tec_norte, sol_norte = by_email('tecnico@norte.example'), by_email('solicitante@norte.example')
    admin_sur, sol_sur = by_email('admin@sur.example'), by_email('solicitante@sur.example')
    pwd = hash_password(DEMO_PASSWORD)

    # --- Hospitales y áreas ---------------------------------------------------------------
    costa = Hospital(name='Clínica Demo Costa', code='CDC-003', tax_id='76.000.333-3',
                     address='Av. Libertad 1180, Viña del Mar', email='contacto@costa.example',
                     phone='+56 32 200 0000', portal_name='Mesa de Ayuda Clínica Costa', color='#0d9488')
    db.add(costa); db.flush()
    for hospital in (norte, sur):
        hospital.created_at = ago(120)
    costa.created_at = ago(75)
    areas = {
        norte: ['Pabellón', 'Pediatría', 'Imagenología', 'Laboratorio', 'Esterilización'],
        sur: ['Urgencias', 'Medicina Interna', 'Esterilización', 'Imagenología'],
        costa: ['Urgencias', 'Pabellón', 'Maternidad', 'Imagenología', 'Laboratorio'],
    }
    for hospital, names in areas.items():
        db.add_all([Department(hospital_id=hospital.id, name=name) for name in names])
    db.flush()
    dept = {(d.hospital_id, d.name): d for d in db.scalars(select(Department))}
    area = lambda hospital, name: dept[(hospital.id, name)].id

    # --- Usuarios ---------------------------------------------------------------------------
    def user(name, email, role, hospital=None, job='', department=None, approval='approved', days=90):
        item = User(name=name, email=email, password_hash=pwd, role=role, job_title=job,
                    hospital_id=hospital.id if hospital else None, approval=approval,
                    department_id=area(hospital, department) if department else None, created_at=ago(days))
        db.add(item)
        return item

    coord_emp = user('Rodrigo Campos', 'coordinador@hospitalops.example', 'coordinador_global', job='Coordinador de servicio técnico')
    tec_emp1 = user('Felipe Araya', 'tecnico1@hospitalops.example', 'tecnico_global', job='Técnico electromedicina senior')
    tec_emp2 = user('Javiera Rojas', 'tecnico2@hospitalops.example', 'tecnico_global', job='Técnica en equipos de soporte vital')
    tec_emp3 = user('Cristóbal Muñoz', 'tecnico3@hospitalops.example', 'tecnico_global', job='Técnico de climatización y gases')
    tec_norte2 = user('Andrés Pérez', 'tecnico2@norte.example', 'tecnico', norte, 'Técnico de mantenimiento')
    med_norte = user('Fernanda Lagos', 'medico@norte.example', 'solicitante', norte, 'Médica intensivista', 'UCI')
    tens_norte = user('Josefa Herrera', 'tens@norte.example', 'solicitante', norte, 'TENS', 'Pediatría')
    img_norte = user('Pablo Reyes', 'imagen@norte.example', 'solicitante', norte, 'Tecnólogo médico', 'Imagenología')
    user('Benjamín Castro', 'pendiente2@norte.example', 'solicitante', norte, 'Auxiliar de aseo', approval='pending', days=2)
    user('Lucas Gutiérrez', 'rechazado@norte.example', 'solicitante', norte, 'Externo', approval='rejected', days=12)
    coord_sur = user('Hernán Vidal', 'coordinador@sur.example', 'coordinador', sur, 'Coordinador de operaciones')
    tec_sur = user('Carolina Núñez', 'tecnico@sur.example', 'tecnico', sur, 'Técnica de mantenimiento')
    sol_sur2 = user('Ignacia Molina', 'enfermera@sur.example', 'solicitante', sur, 'Enfermera', 'Urgencias')
    user('Gabriel Sepúlveda', 'pendiente@sur.example', 'solicitante', sur, 'TENS', approval='pending', days=1)
    admin_costa = user('Martina Silva', 'admin@costa.example', 'admin_cliente', costa, 'Gerenta de operaciones', days=75)
    coord_costa = user('Sebastián Torres', 'coordinador@costa.example', 'coordinador', costa, 'Jefe de mantenimiento', days=74)
    tec_costa = user('Daniela Fuentes', 'tecnico@costa.example', 'tecnico', costa, 'Técnica electromedicina', days=74)
    sol_costa = user('Catalina Vega', 'solicitante@costa.example', 'solicitante', costa, 'Matrona', 'Maternidad', days=70)
    sol_costa2 = user('Joaquín Ortiz', 'urgencias@costa.example', 'solicitante', costa, 'Enfermero', 'Urgencias', days=60)
    user('Florencia Pizarro', 'pendiente@costa.example', 'solicitante', costa, 'Tecnóloga médica', approval='pending', days=3)
    # Personal adicional: 20 por hospital (1 coordinador, 2 técnicos, 14 solicitantes y 3 pendientes de aprobación)
    for hospital, staff_rows in additional_staff(norte, sur, costa).items():
        for index, (name, job, department) in enumerate(staff_rows):
            role = 'coordinador' if index == 0 else 'tecnico' if index < 3 else 'solicitante'
            approval = 'pending' if index >= 17 else 'approved'
            user(name, demo_email(name, hospital), role, hospital, job, department, approval,
                 days=index % 4 + 1 if approval == 'pending' else 85 - index * 3)
    db.flush()
    admins = {norte.id: admin_norte, sur.id: admin_sur, costa.id: admin_costa}

    # --- Equipos (activos) ------------------------------------------------------------------
    asset_rows = [
        (norte, 'EQ-VEN-003', 'Ventilador mecánico Hamilton C3', 'Soporte vital', 'UCI · Box 1', 'VEN-77120'),
        (norte, 'EQ-DEF-004', 'Desfibrilador bifásico', 'Electromedicina', 'Urgencias · Reanimador', 'DEF-30045'),
        (norte, 'EQ-ECO-005', 'Ecógrafo portátil', 'Imagenología', 'Imagenología · Sala 2', 'ECO-58210'),
        (norte, 'EQ-AUT-006', 'Autoclave de vapor 250 L', 'Esterilización', 'Esterilización', 'AUT-11873'),
        (norte, 'EQ-INC-007', 'Incubadora neonatal', 'Soporte vital', 'Pediatría · Neonatología', 'INC-40991'),
        (norte, 'EQ-CAM-008', 'Cama eléctrica UCI', 'Mobiliario clínico', 'UCI · Box 4', 'CAM-66502'),
        (norte, 'EQ-RX-009', 'Equipo de rayos X móvil', 'Imagenología', 'Imagenología', 'RX-20877'),
        (sur, 'EQ-MON-101', 'Monitor de signos vitales', 'Electromedicina', 'Medicina Interna · Sala 3', 'MON-81230'),
        (sur, 'EQ-CLI-102', 'Unidad de climatización pabellón', 'Climatización', 'Pabellón', 'CLI-00412'),
        (sur, 'EQ-AUT-103', 'Autoclave de mesa', 'Esterilización', 'Esterilización', 'AUT-55190'),
        (sur, 'EQ-BOM-104', 'Bomba de infusión', 'Electromedicina', 'Urgencias', 'BOM-12093'),
        (costa, 'EQ-MON-201', 'Monitor fetal', 'Electromedicina', 'Maternidad · Box 2', 'MFE-90311'),
        (costa, 'EQ-DEF-202', 'Desfibrilador DEA', 'Electromedicina', 'Urgencias', 'DEA-71002'),
        (costa, 'EQ-MES-203', 'Mesa quirúrgica eléctrica', 'Mobiliario clínico', 'Pabellón 1', 'MES-31570'),
        (costa, 'EQ-ECO-204', 'Ecógrafo Doppler', 'Imagenología', 'Imagenología', 'ECO-62014'),
        (costa, 'EQ-VEN-205', 'Ventilador de transporte', 'Soporte vital', 'Urgencias', 'VEN-18834', False),
    ]
    assets = {}
    for hospital, code, name, category, location, serial, *active in asset_rows:
        assets[code] = Asset(hospital_id=hospital.id, code=code, name=name, category=category,
                             location=location, serial_number=serial, active=active[0] if active else True)
    db.add_all(assets.values()); db.flush()

    # --- Tickets con comentarios ------------------------------------------------------------
    # (hospital, solicitante, asignado, estado, prioridad, categoría, título, descripción, ubicación, equipo, días, comentarios)
    ticket_rows = [
        (norte, med_norte, tec_emp1, 'en_proceso', 'critica', 'Soporte vital', 'Ventilador UCI con alarma de presión alta',
         'El ventilador del box 1 activa alarma de presión alta sin causa clínica aparente. Paciente trasladado a equipo de respaldo.',
         'UCI · Box 1', 'EQ-VEN-003', 2, [(tec_emp1, 'En terreno. Se detecta sensor de flujo con lecturas erráticas; se reemplazará.', False),
                                          (coord_emp, 'Prioridad máxima: equipo de soporte vital. Mantener respaldo hasta validación.', True)]),
        (norte, sol_norte, tec_norte, 'abierto', 'alta', 'Electromedicina', 'Desfibrilador no supera autotest diario',
         'En el chequeo de turno el desfibrilador de reanimador muestra error de autotest de batería.',
         'Urgencias · Reanimador', 'EQ-DEF-004', 1, [(admin_norte, 'Ticket confirmado. Se deja DEA de respaldo en el reanimador.', False)]),
        (norte, img_norte, tec_emp2, 'en_proceso', 'media', 'Imagenología', 'Ecógrafo portátil con imagen intermitente',
         'La imagen se congela al mover el transductor lineal. Ocurre varias veces por turno.',
         'Imagenología · Sala 2', 'EQ-ECO-005', 5, [(tec_emp2, 'Probable falla del cable del transductor. Se solicita repuesto a bodega.', False),
                                                     (tec_emp2, 'Cliente aprobó cotización del transductor.', True)]),
        (norte, sol_norte, tec_norte, 'resuelto', 'media', 'Esterilización', 'Autoclave no alcanza temperatura de ciclo',
         'El ciclo de 134 °C se aborta a los 20 minutos por baja temperatura.', 'Esterilización', 'EQ-AUT-006', 12,
         [(tec_norte, 'Se reemplazó la resistencia y se realizó prueba Bowie-Dick con resultado conforme.', False)]),
        (norte, tens_norte, tec_emp1, 'cerrado', 'alta', 'Soporte vital', 'Incubadora neonatal no mantiene humedad',
         'La humedad relativa cae bajo 50 % aunque el depósito está lleno.', 'Pediatría · Neonatología', 'EQ-INC-007', 20,
         [(tec_emp1, 'Se cambió el módulo humidificador y se calibró el sensor.', False),
          (tens_norte, 'Funcionando correctamente, gracias.', False)]),
        (norte, med_norte, None, 'pendiente', 'media', 'Mobiliario clínico', 'Cama eléctrica UCI no baja respaldo',
         'El control del respaldo no responde; el resto de funciones opera bien.', 'UCI · Box 4', 'EQ-CAM-008', 0, []),
        (norte, tens_norte, None, 'pendiente', 'baja', 'Infraestructura', 'Luminaria parpadea en sala de procedimientos',
         'Tubo fluorescente parpadea en forma constante.', 'Pediatría · Procedimientos', None, 1, []),
        (norte, img_norte, tec_emp3, 'abierto', 'alta', 'Imagenología', 'Rayos X móvil no carga batería',
         'El equipo indica batería baja aun después de toda la noche conectado.', 'Imagenología', 'EQ-RX-009', 3, []),
        (norte, sol_norte, None, 'rechazado', 'baja', 'Soporte', 'Solicitud de cambio de mouse',
         'El mouse del computador de enfermería está desgastado.', 'Urgencias', None, 9,
         [(admin_norte, 'Rechazado: corresponde a la mesa de ayuda de informática, no a mantenimiento clínico.', False)]),
        (norte, med_norte, tec_norte2, 'cerrado', 'media', 'Gases clínicos', 'Fuga en toma de oxígeno box 2',
         'Se escucha fuga en la toma mural de oxígeno al conectar el flujómetro.', 'UCI · Box 2', None, 28,
         [(tec_norte2, 'Se cambió el o-ring de la toma y se verificó con solución jabonosa.', False)]),
        (norte, sol_norte, tec_norte2, 'resuelto', 'baja', 'Infraestructura', 'Puerta automática de urgencias lenta',
         'La puerta tarda en abrir y a veces se queda a medio camino.', 'Urgencias · Acceso', None, 6,
         [(tec_norte2, 'Se ajustó el sensor y se lubricó el riel.', False)]),
        (sur, sol_sur2, tec_sur, 'en_proceso', 'alta', 'Electromedicina', 'Bomba de infusión marca oclusión sin motivo',
         'La bomba de urgencias detiene la infusión con alarma de oclusión aguas abajo.', 'Urgencias', 'EQ-BOM-104', 2,
         [(tec_sur, 'Se retiró el equipo para pruebas de presión en taller.', False)]),
        (sur, sol_sur, tec_emp3, 'abierto', 'critica', 'Climatización', 'Pabellón sin control de humedad',
         'La humedad del pabellón supera el 65 % desde ayer. Se suspendieron cirugías electivas.', 'Pabellón', 'EQ-CLI-102', 1,
         [(coord_sur, 'Se reprogramaron dos cirugías. Se solicitó apoyo al técnico de empresa.', True)]),
        (sur, sol_sur2, None, 'pendiente', 'media', 'Electromedicina', 'Monitor de sala 3 sin curva de ECG',
         'El monitor muestra frecuencia cardiaca pero no la curva.', 'Medicina Interna · Sala 3', 'EQ-MON-101', 0, []),
        (sur, sol_sur, tec_sur, 'cerrado', 'media', 'Esterilización', 'Autoclave de mesa con fuga de vapor',
         'Escapa vapor por la puerta durante el ciclo.', 'Esterilización', 'EQ-AUT-103', 25,
         [(tec_sur, 'Se reemplazó el empaque de la puerta.', False)]),
        (sur, sol_sur2, tec_sur, 'resuelto', 'baja', 'Infraestructura', 'Enchufe suelto en estación de enfermería',
         'Enchufe doble con la placa suelta.', 'Urgencias', None, 8, []),
        (costa, sol_costa, tec_emp2, 'en_proceso', 'alta', 'Electromedicina', 'Monitor fetal imprime registro en blanco',
         'El registro de cardiotocografía sale sin trazado.', 'Maternidad · Box 2', 'EQ-MON-201', 3,
         [(tec_emp2, 'Cabezal térmico sucio; se limpia y se prueba con papel nuevo.', False)]),
        (costa, sol_costa2, tec_costa, 'abierto', 'critica', 'Electromedicina', 'DEA de urgencias con electrodos vencidos',
         'En la revisión semanal se detectan electrodos vencidos y sin reposición en bodega.', 'Urgencias', 'EQ-DEF-202', 1, []),
        (costa, sol_costa, None, 'pendiente', 'alta', 'Mobiliario clínico', 'Mesa quirúrgica no cambia a Trendelenburg',
         'La mesa no responde al comando de inclinación.', 'Pabellón 1', 'EQ-MES-203', 0, []),
        (costa, sol_costa2, tec_costa, 'cerrado', 'media', 'Imagenología', 'Ecógrafo Doppler se reinicia solo',
         'El equipo se reinicia cada 30 a 40 minutos de uso.', 'Imagenología', 'EQ-ECO-204', 30,
         [(tec_costa, 'Se reemplazó la fuente de poder y se actualizó el firmware.', False)]),
        (costa, sol_costa, tec_costa, 'resuelto', 'baja', 'Infraestructura', 'Llave de lavamanos gotea en maternidad',
         'Goteo constante en lavamanos de la sala de partos.', 'Maternidad', None, 4, []),
        (costa, sol_costa2, None, 'rechazado', 'media', 'Soporte', 'Instalar televisor en sala de espera',
         'Solicito instalar un televisor en la sala de espera de urgencias.', 'Urgencias · Espera', None, 15,
         [(admin_costa, 'Rechazado: no corresponde a mantenimiento; derivar a administración.', False)]),
    ]
    tickets = []
    for (hospital, requester, assignee, status, priority, category, title, description,
         location, asset_code, days, comments) in ticket_rows:
        created = ago(days, 6)
        confirmed = status not in ('pendiente', 'rechazado')
        ticket = Ticket(hospital_id=hospital.id, requester_id=requester.id,
                        assignee_id=assignee.id if assignee else None,
                        confirmed_by_id=admins[hospital.id].id if confirmed else None,
                        confirmed_at=created + timedelta(hours=1) if confirmed else None,
                        title=title, description=description, category=category, priority=priority,
                        status=status, location=location, asset_id=assets[asset_code].id if asset_code else None,
                        created_at=created, updated_at=created + timedelta(hours=3))
        db.add(ticket); db.flush()
        tickets.append(ticket)
        for offset, (author, body, internal) in enumerate(comments, start=2):
            db.add(TicketComment(ticket_id=ticket.id, author_id=author.id, body=body, internal=internal,
                                 created_at=created + timedelta(hours=offset)))
        db.add(AuditLog(hospital_id=hospital.id, actor_id=requester.id, action='crear', entity='ticket',
                        entity_id=ticket.id, detail=title, created_at=created))
        if confirmed:
            db.add(AuditLog(hospital_id=hospital.id, actor_id=admins[hospital.id].id, action='confirmar',
                            entity='ticket', entity_id=ticket.id, detail='Ticket confirmado', created_at=created + timedelta(hours=1)))
    # Los tickets del seed base se reparten en los últimos días para que el panel se vea realista
    for ticket_id, days in ((1, 4), (2, 1), (3, 10), (4, 0)):
        base_ticket = db.get(Ticket, ticket_id)
        base_ticket.created_at = base_ticket.updated_at = ago(days, 2)

    # --- Inventario por hospital con Kardex ---------------------------------------------------
    # (hospital, sku, producto, categoría, ubicación, costo, precio, stock inicial, mínimo)
    inventory_rows = [
        (norte, 'INS-MAS-004', 'Mascarilla quirúrgica caja 50', 'Insumos', 'Bodega central', 3900, 5900, 120, 30),
        (norte, 'INS-ALC-005', 'Alcohol gel 1 L', 'Insumos', 'Bodega central', 2800, 4200, 60, 20),
        (norte, 'INS-GAS-006', 'Gasa estéril 10x10 paquete', 'Insumos', 'Bodega central', 450, 790, 400, 100),
        (norte, 'INS-CAT-007', 'Catéter venoso periférico 20G', 'Insumos', 'Farmacia', 520, 900, 300, 80),
        (norte, 'INS-ELE-008', 'Electrodo ECG adulto', 'Insumos', 'Electromedicina', 95, 180, 900, 200),
        (norte, 'INS-PAP-009', 'Papel registro ECG 80 mm', 'Insumos', 'Electromedicina', 2100, 3500, 25, 15),
        (norte, 'REP-BAT-010', 'Batería monitor multiparámetro', 'Repuestos', 'Electromedicina', 48000, 72000, 4, 3),
        (norte, 'REP-CAB-011', 'Cable troncal ECG 5 derivaciones', 'Repuestos', 'Electromedicina', 36000, 54000, 5, 4),
        (norte, 'REP-FIL-012', 'Filtro HEPA ventilador', 'Repuestos', 'UCI', 18500, 27500, 12, 6),
        (norte, 'REP-SEN-013', 'Sensor de flujo ventilador', 'Repuestos', 'UCI', 62000, 89000, 3, 2),
        (norte, 'EPP-DEL-014', 'Delantal desechable', 'EPP', 'Bodega central', 350, 650, 500, 150),
        (norte, 'EPP-ANT-015', 'Antiparras de protección', 'EPP', 'Bodega central', 2900, 4500, 40, 15),
        (norte, 'EST-IND-016', 'Indicador biológico autoclave', 'Esterilización', 'Esterilización', 4100, 6200, 30, 20),
        (norte, 'EST-BOL-017', 'Bolsa de esterilización 15x30', 'Esterilización', 'Esterilización', 85, 160, 1200, 300),
        (sur, 'SUR-MAS-002', 'Mascarilla N95', 'EPP', 'Bodega sur', 890, 1500, 200, 60),
        (sur, 'SUR-JER-003', 'Jeringa 10 ml', 'Insumos', 'Bodega sur', 210, 380, 350, 100),
        (sur, 'SUR-SUE-004', 'Suero fisiológico 500 ml', 'Insumos', 'Farmacia', 750, 1200, 180, 60),
        (sur, 'SUR-ELE-005', 'Electrodo ECG adulto', 'Insumos', 'Bodega sur', 95, 180, 300, 150),
        (sur, 'SUR-FIL-006', 'Filtro climatización pabellón', 'Repuestos', 'Mantenimiento', 32000, 46000, 4, 3),
        (sur, 'SUR-EMP-007', 'Empaque puerta autoclave', 'Repuestos', 'Mantenimiento', 27500, 39000, 3, 2),
        (sur, 'SUR-IND-008', 'Indicador químico clase 5', 'Esterilización', 'Esterilización', 160, 290, 600, 200),
        (costa, 'CDC-GUA-001', 'Guantes estériles 7.0 par', 'Insumos', 'Bodega clínica', 390, 650, 500, 150),
        (costa, 'CDC-ELE-002', 'Electrodos DEA adulto', 'Repuestos', 'Urgencias', 21000, 32000, 3, 4),
        (costa, 'CDC-PAP-003', 'Papel monitor fetal', 'Insumos', 'Maternidad', 3200, 4900, 18, 10),
        (costa, 'CDC-GEL-004', 'Gel de ultrasonido 5 L', 'Insumos', 'Imagenología', 6900, 9800, 9, 4),
        (costa, 'CDC-CAT-005', 'Catéter venoso periférico 18G', 'Insumos', 'Farmacia', 540, 920, 260, 80),
        (costa, 'CDC-MAS-006', 'Mascarilla quirúrgica caja 50', 'Insumos', 'Bodega clínica', 3900, 5900, 70, 25),
        (costa, 'CDC-SAB-007', 'Sábana quirúrgica desechable', 'Insumos', 'Pabellón', 1450, 2300, 140, 50),
        (costa, 'CDC-BAT-008', 'Batería mesa quirúrgica', 'Repuestos', 'Pabellón', 89000, 125000, 2, 1),
        (costa, 'CDC-ALC-009', 'Alcohol gel 1 L', 'Insumos', 'Bodega clínica', 2800, 4200, 35, 20),
    ]
    staff = {norte.id: coord_norte, sur.id: coord_sur, costa.id: coord_costa}
    movement_plan = (('salida', 0.25, 'Consumo de servicios clínicos', 45),
                     ('entrada', 0.30, 'Recepción orden de compra', 35),
                     ('salida', 0.30, 'Reposición a unidades', 25),
                     ('salida', 0.15, 'Consumo de servicios clínicos', 18))
    stock_items = []
    for index, (hospital, sku, name, category, location, cost, price, initial, minimum) in enumerate(inventory_rows, start=1):
        item = InventoryItem(hospital_id=hospital.id, sku=sku, barcode=f'78010000{hospital.id}{index:04d}',
                             name=name, category=category, location=location, gross_cost=Decimal(cost),
                             sale_price=Decimal(price), stock=initial, min_stock=minimum, created_at=ago(60))
        db.add(item); db.flush()
        db.add(InventoryMovement(hospital_id=hospital.id, item_id=item.id, actor_id=admins[hospital.id].id,
                                 kind='inicial', delta=initial, resulting_stock=initial,
                                 note='Carga inicial de inventario', created_at=ago(60)))
        for kind, share, note, days in movement_plan:
            amount = max(1, round(initial * share)) if initial >= 4 else 0
            if not amount or (kind == 'salida' and amount > item.stock):
                continue
            item.stock += amount if kind == 'entrada' else -amount
            db.add(InventoryMovement(hospital_id=hospital.id, item_id=item.id, actor_id=staff[hospital.id].id,
                                     kind=kind, delta=amount if kind == 'entrada' else -amount,
                                     resulting_stock=item.stock, note=note, created_at=ago(days)))
        stock_items.append(item)
    # El historial inicial del seed base queda fechado al comienzo del período
    for move in db.scalars(select(InventoryMovement).where(InventoryMovement.note == 'Datos de demostración')):
        move.created_at = ago(60)

    # Conteo físico cerrado (con diferencias) y uno abierto listo para la demo en Hospital Norte
    norte_items = [i for i in stock_items if i.hospital_id == norte.id]
    closed = StockCount(hospital_id=norte.id, created_by_id=coord_norte.id, status='cerrado',
                        note='Inventario mensual septiembre', created_at=ago(12), closed_at=ago(11))
    db.add(closed); db.flush()
    differences = {'INS-GAS-006': -6, 'EPP-DEL-014': -10, 'INS-ELE-008': 4}
    for item in norte_items:
        actual = item.stock + differences.get(item.sku, 0)
        db.add(StockCountLine(stock_count_id=closed.id, item_id=item.id, expected_stock=item.stock, actual_stock=actual))
        if actual != item.stock:
            db.add(InventoryMovement(hospital_id=norte.id, item_id=item.id, actor_id=coord_norte.id, kind='conteo',
                                     delta=actual - item.stock, resulting_stock=actual,
                                     note=f'Ajuste inventario físico #{closed.id}', created_at=ago(11)))
            item.stock = actual
    db.add(AuditLog(hospital_id=norte.id, actor_id=coord_norte.id, action='cerrar', entity='conteo',
                    entity_id=closed.id, detail=f'{len(norte_items)} líneas verificadas', created_at=ago(11)))
    db.flush()
    open_count = StockCount(hospital_id=norte.id, created_by_id=coord_norte.id, note='Conteo trimestral bodega central',
                            created_at=ago(0, 3))
    db.add(open_count); db.flush()
    for item in db.scalars(select(InventoryItem).where(InventoryItem.hospital_id == norte.id,
                                                      InventoryItem.active.is_(True)).order_by(InventoryItem.name)):
        db.add(StockCountLine(stock_count_id=open_count.id, item_id=item.id, expected_stock=item.stock))

    # --- Bodega de la empresa proveedora y stock por técnico ------------------------------------
    # (sku, repuesto, categoría, ubicación, costo, precio, stock inicial, mínimo)
    provider_rows = [
        ('PRV-SPO-001', 'Sensor SpO2 adulto reutilizable', 'Sensores', 'Estante A1', 38000, 59000, 30, 8),
        ('PRV-SPO-002', 'Sensor SpO2 pediátrico', 'Sensores', 'Estante A1', 41000, 63000, 12, 5),
        ('PRV-FLU-003', 'Sensor de flujo ventilador', 'Sensores', 'Estante A2', 62000, 92000, 10, 4),
        ('PRV-BAT-004', 'Batería monitor multiparámetro', 'Baterías', 'Estante B1', 48000, 74000, 14, 6),
        ('PRV-BAT-005', 'Batería desfibrilador', 'Baterías', 'Estante B1', 135000, 189000, 5, 3),
        ('PRV-BAT-006', 'Batería rayos X móvil', 'Baterías', 'Estante B2', 420000, 560000, 2, 2),
        ('PRV-CAB-007', 'Cable troncal ECG 5 derivaciones', 'Cables', 'Estante C1', 36000, 55000, 20, 6),
        ('PRV-CAB-008', 'Transductor lineal ecógrafo', 'Transductores', 'Bodega segura', 1450000, 1890000, 2, 1),
        ('PRV-HEP-009', 'Filtro HEPA ventilador', 'Filtros', 'Estante D1', 18500, 28000, 40, 15),
        ('PRV-HEP-010', 'Filtro climatización pabellón F9', 'Filtros', 'Estante D2', 32000, 47000, 8, 6),
        ('PRV-KIT-011', 'Kit mantención preventiva bomba infusión', 'Kits de mantención', 'Estante E1', 27000, 42000, 18, 6),
        ('PRV-KIT-012', 'Kit mantención autoclave', 'Kits de mantención', 'Estante E1', 84000, 119000, 6, 3),
        ('PRV-RES-013', 'Resistencia calefactora autoclave', 'Repuestos eléctricos', 'Estante E2', 96000, 138000, 3, 2),
        ('PRV-FUE-014', 'Fuente de poder ecógrafo', 'Repuestos eléctricos', 'Estante E2', 210000, 295000, 2, 2),
        ('PRV-HUM-015', 'Módulo humidificador incubadora', 'Repuestos', 'Estante F1', 175000, 248000, 3, 1),
        ('PRV-ORI-016', 'Set o-rings tomas de gases', 'Gases clínicos', 'Estante F2', 9500, 15000, 50, 20),
        ('PRV-ELE-017', 'Electrodos DEA adulto (par)', 'Consumibles técnicos', 'Estante G1', 21000, 33000, 16, 10),
        ('PRV-CAB-018', 'Cabezal térmico monitor fetal', 'Repuestos', 'Estante G2', 128000, 176000, 1, 2),
    ]
    provider = {}
    for sku, name, category, location, cost, price, initial, minimum in provider_rows:
        item = ProviderItem(sku=sku, name=name, category=category, location=location, gross_cost=Decimal(cost),
                            sale_price=Decimal(price), stock=initial, min_stock=minimum, created_at=ago(90))
        db.add(item); db.flush()
        provider[sku] = item
        db.add(ProviderMovement(item_id=item.id, actor_id=coord_emp.id, kind='entrada', quantity=initial,
                                note='Ingreso inicial a bodega', created_at=ago(90)))

    def assign(sku, technician, qty, days):
        item = provider[sku]
        item.stock -= qty
        allocation = db.scalar(select(TechnicianStock).where(TechnicianStock.item_id == item.id,
                                                            TechnicianStock.technician_id == technician.id))
        if allocation is None:
            allocation = TechnicianStock(item_id=item.id, technician_id=technician.id, quantity=0)
            db.add(allocation)
        allocation.quantity += qty
        db.add(ProviderMovement(item_id=item.id, technician_id=technician.id, actor_id=coord_emp.id,
                                kind='asignacion', quantity=qty, note='Entrega a técnico', created_at=ago(days)))
        db.add(AuditLog(hospital_id=None, actor_id=coord_emp.id, action='entrega', entity='bodega_producto',
                        entity_id=item.id, detail=f'{qty} unidades -> {technician.name}', created_at=ago(days)))
        db.flush()
        return allocation

    def consume(sku, technician, qty, ticket, note, days):
        allocation = db.scalar(select(TechnicianStock).where(TechnicianStock.item_id == provider[sku].id,
                                                            TechnicianStock.technician_id == technician.id))
        allocation.quantity -= qty
        db.add(ProviderMovement(item_id=provider[sku].id, technician_id=technician.id, actor_id=technician.id,
                                ticket_id=ticket.id, hospital_id=ticket.hospital_id, kind='consumo',
                                quantity=qty, note=note, created_at=ago(days)))
        db.add(AuditLog(hospital_id=ticket.hospital_id, actor_id=technician.id, action='consumo', entity='bodega_producto',
                        entity_id=provider[sku].id, detail=f'{qty} unidades en ticket {ticket.id}', created_at=ago(days)))

    for sku, technician, qty, days in [
        ('PRV-SPO-001', tec_emp1, 6, 40), ('PRV-FLU-003', tec_emp1, 3, 40), ('PRV-HEP-009', tec_emp1, 10, 40),
        ('PRV-HUM-015', tec_emp1, 1, 22), ('PRV-BAT-004', tec_emp1, 2, 15), ('PRV-ORI-016', tec_emp1, 10, 15),
        ('PRV-CAB-007', tec_emp2, 4, 38), ('PRV-CAB-008', tec_emp2, 1, 4), ('PRV-KIT-011', tec_emp2, 5, 30),
        ('PRV-SPO-002', tec_emp2, 3, 30), ('PRV-CAB-018', tec_emp2, 1, 3),
        ('PRV-HEP-010', tec_emp3, 4, 20), ('PRV-BAT-006', tec_emp3, 1, 2), ('PRV-ORI-016', tec_emp3, 8, 20),
        ('PRV-KIT-012', tec_emp3, 2, 18), ('PRV-ELE-017', tec_emp3, 4, 10),
    ]:
        assign(sku, technician, qty, days)
    ticket_by_title = {t.title: t for t in tickets}
    consume('PRV-FLU-003', tec_emp1, 1, ticket_by_title['Ventilador UCI con alarma de presión alta'], 'Reemplazo de sensor de flujo', 1)
    consume('PRV-HEP-009', tec_emp1, 2, ticket_by_title['Ventilador UCI con alarma de presión alta'], 'Cambio de filtros en mantención correctiva', 1)
    consume('PRV-CAB-008', tec_emp2, 1, ticket_by_title['Ecógrafo portátil con imagen intermitente'], 'Reemplazo de transductor lineal', 2)
    consume('PRV-HEP-010', tec_emp3, 2, ticket_by_title['Pabellón sin control de humedad'], 'Cambio de filtros F9 de la UMA', 0)
    # Devolución de material no utilizado
    provider['PRV-SPO-001'].stock += 2
    db.scalar(select(TechnicianStock).where(TechnicianStock.item_id == provider['PRV-SPO-001'].id,
                                            TechnicianStock.technician_id == tec_emp1.id)).quantity -= 2
    db.add(ProviderMovement(item_id=provider['PRV-SPO-001'].id, technician_id=tec_emp1.id, actor_id=coord_emp.id,
                            kind='devolucion', quantity=2, note='Devolución a bodega', created_at=ago(7)))
    # Reposición de proveedor externo
    provider['PRV-HEP-009'].stock += 20
    db.add(ProviderMovement(item_id=provider['PRV-HEP-009'].id, actor_id=coord_emp.id, kind='entrada', quantity=20,
                            note='Orden de compra OC-2026-0912', created_at=ago(9)))

    # --- CRM ------------------------------------------------------------------------------------
    contact_rows = [
        (norte, 'Rocío Bravo', 'rocio.bravo@example.org', '+56 9 5555 3333', 'Jefa de UCI', 'Unidad de Paciente Crítico'),
        (norte, 'Alejandro Espinoza', 'a.espinoza@example.org', '+56 9 5555 4444', 'Subdirector administrativo', 'Dirección'),
        (norte, 'Paula Contreras', 'paula.c@example.org', '+56 9 5555 5555', 'Jefa de esterilización', 'Esterilización'),
        (sur, 'Marcelo Jara', 'marcelo.jara@example.org', '+56 9 5555 6666', 'Director de operaciones', 'Dirección'),
        (sur, 'Camila Riquelme', 'c.riquelme@example.org', '+56 9 5555 7777', 'Encargada de pabellón', 'Pabellón'),
        (costa, 'Verónica Alarcón', 'v.alarcon@example.org', '+56 9 5555 8888', 'Gerenta de compras', 'Abastecimiento'),
        (costa, 'Tomás Navarro', 't.navarro@example.org', '+56 9 5555 9999', 'Jefe de imagenología', 'Imagenología'),
        (costa, 'Isidora Cárdenas', 'i.cardenas@example.org', '+56 9 5444 1111', 'Matrona supervisora', 'Maternidad'),
    ]
    contacts = {}
    for hospital, name, email, phone, job, department in contact_rows:
        contacts[name] = CRMContact(hospital_id=hospital.id, name=name, email=email, phone=phone,
                                    job_title=job, department=department, created_at=ago(50))
    db.add_all(contacts.values()); db.flush()
    owners = {norte.id: coord_norte, sur.id: coord_sur, costa.id: coord_costa}
    # (hospital, contacto, oportunidad, valor CLP, etapa, cierre esperado, notas)
    opportunity_rows = [
        (norte, 'Rocío Bravo', 'Contrato de mantención de ventiladores UCI', 14500000, 'negociacion', '2026-11-20', 'Incluye 6 ventiladores y 2 visitas preventivas al año.'),
        (norte, 'Alejandro Espinoza', 'Renovación parque de monitores', 32000000, 'propuesta', '2026-12-15', 'Licitación interna; competencia de dos proveedores.'),
        (norte, 'Paula Contreras', 'Mantención preventiva de autoclaves', 4200000, 'ganado', '2026-09-30', 'Firmado por 12 meses.'),
        (norte, 'Rocío Bravo', 'Capacitación uso de desfibriladores', 850000, 'nuevo', '2027-01-15', ''),
        (norte, 'Alejandro Espinoza', 'Arriendo de rayos X móvil', 9600000, 'perdido', '2026-08-31', 'Se adjudicó a otro proveedor por precio.'),
        (sur, 'Marcelo Jara', 'Plan anual de climatización de pabellones', 11800000, 'propuesta', '2026-11-30', 'Requiere visita técnica previa.'),
        (sur, 'Camila Riquelme', 'Recambio de filtros HEPA pabellón', 2300000, 'contactado', '2026-12-05', ''),
        (sur, 'Marcelo Jara', 'Mantención bombas de infusión (20 unidades)', 5600000, 'ganado', '2026-09-15', 'Inicio de servicio en octubre.'),
        (costa, 'Verónica Alarcón', 'Contrato integral de electromedicina', 27500000, 'negociacion', '2026-12-01', 'Cliente pide SLA de 4 horas para equipos críticos.'),
        (costa, 'Tomás Navarro', 'Soporte de ecógrafos Doppler', 6900000, 'contactado', '2026-12-20', ''),
        (costa, 'Isidora Cárdenas', 'Reposición de monitores fetales', 15400000, 'nuevo', '2027-02-28', 'Interés en 3 equipos nuevos.'),
        (costa, 'Verónica Alarcón', 'Suministro de electrodos DEA', 1250000, 'ganado', '2026-10-01', 'Entrega mensual.'),
    ]
    for hospital, contact, name, value, stage, close, notes in opportunity_rows:
        db.add(CRMOpportunity(hospital_id=hospital.id, contact_id=contacts[contact].id, owner_id=owners[hospital.id].id,
                              name=name, value=Decimal(value), stage=stage, expected_close=close, notes=notes,
                              created_at=ago(45)))

    # --- Bitácora general ---------------------------------------------------------------------
    db.add_all([
        AuditLog(hospital_id=costa.id, actor_id=root.id, action='crear', entity='hospital', entity_id=costa.id,
                 detail='Alta de cliente Clínica Demo Costa', created_at=ago(75)),
        AuditLog(hospital_id=norte.id, actor_id=admin_norte.id, action='aprobar', entity='usuario', entity_id=med_norte.id,
                 detail='Cuenta aprobada: medico@norte.example', created_at=ago(88)),
        AuditLog(hospital_id=norte.id, actor_id=admin_norte.id, action='rechazar', entity='usuario', entity_id=None,
                 detail='Cuenta rechazada: rechazado@norte.example', created_at=ago(11)),
        AuditLog(hospital_id=costa.id, actor_id=admin_costa.id, action='editar', entity='configuración', entity_id=costa.id,
                 detail='Color y nombre del portal actualizados', created_at=ago(70)),
        AuditLog(hospital_id=None, actor_id=coord_emp.id, action='entrada', entity='bodega_producto',
                 entity_id=provider['PRV-HEP-009'].id, detail='+20 — Orden de compra OC-2026-0912', created_at=ago(9)),
    ])
    db.commit()
    return True
