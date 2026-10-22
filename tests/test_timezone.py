from datetime import datetime
from sqlalchemy import select
from app import main
from app.models import AuditLog, Ticket, User
from test_app import sandbox, signin


def test_format_local_follows_chile_daylight_saving():
    # Horario de verano (UTC-3) e invierno (UTC-4); las fechas se guardan en UTC sin zona
    assert main.format_local(datetime(2026, 1, 15, 15, 0)) == '15/01/2026 12:00'
    assert main.format_local(datetime(2026, 7, 15, 15, 0)) == '15/07/2026 11:00'
    # Un evento de madrugada UTC pertenece al día anterior en Chile
    assert main.format_local(datetime(2026, 10, 9, 2, 30), '%d/%m/%Y') == '08/10/2026'
    assert main.format_local(None) == ''


def test_pages_show_chile_time(sandbox):
    client, Session = sandbox
    with Session() as db:
        db.get(Ticket, 1).created_at = datetime(2026, 1, 15, 15, 0)
        db.commit()
    signin(client, 'admin@norte.example')
    html = client.get('/tickets/1').text
    assert '15/01/2026 a las 12:00' in html and '15:00' not in html


def test_company_audit_date_filter_uses_local_days(sandbox):
    client, Session = sandbox
    with Session() as db:
        root = db.scalar(select(User).where(User.email == 'root@hospitalops.example'))
        # 09/10 02:30 UTC = 08/10 23:30 en Chile
        db.add(AuditLog(actor_id=root.id, hospital_id=None, action='prueba', entity='zona_horaria',
                        detail='Evento nocturno', created_at=datetime(2026, 10, 9, 2, 30)))
        db.commit()
    signin(client, 'root@hospitalops.example')
    assert 'Evento nocturno' in client.get('/auditoria-empresa?desde=2026-10-08&hasta=2026-10-08').text
    assert 'Evento nocturno' not in client.get('/auditoria-empresa?desde=2026-10-09').text
    assert '08/10/2026 23:30' in client.get('/auditoria-empresa?entidad=zona_horaria').text
