from sqlalchemy import func, select
from app.models import (InventoryItem, InventoryMovement, ProviderItem, ProviderMovement, TechnicianStock,
                        Ticket, User)
from seed_demo import seed_demo
from test_app import sandbox, signin


def test_demo_seed_is_consistent_and_idempotent(sandbox):
    _, Session = sandbox
    with Session() as db:
        assert seed_demo(db) is True
        assert seed_demo(db) is False
        assert db.scalar(select(func.count()).select_from(User)) == 88
        assert db.scalar(select(func.count()).select_from(Ticket)) == 26
        # El Kardex de cada producto suma exactamente su stock actual
        for item in db.scalars(select(InventoryItem)):
            total = db.scalar(select(func.sum(InventoryMovement.delta)).where(InventoryMovement.item_id == item.id))
            assert total == item.stock, item.sku
        # Bodega: stock central y stock en manos de técnicos cuadran con los movimientos
        for item in db.scalars(select(ProviderItem)):
            moved = lambda kind: db.scalar(select(func.coalesce(func.sum(ProviderMovement.quantity), 0)).where(
                ProviderMovement.item_id == item.id, ProviderMovement.kind == kind))
            held = db.scalar(select(func.coalesce(func.sum(TechnicianStock.quantity), 0))
                             .where(TechnicianStock.item_id == item.id))
            assert item.stock == moved('entrada') - moved('asignacion') + moved('devolucion'), item.sku
            assert held == moved('asignacion') - moved('devolucion') - moved('consumo'), item.sku


def test_demo_accounts_can_sign_in(sandbox):
    client, Session = sandbox
    with Session() as db:
        seed_demo(db)
    for email, page in [('coordinador@hospitalops.example', '/operaciones/tickets'),
                        ('tecnico1@hospitalops.example', '/mis-repuestos'),
                        ('admin@costa.example', '/dashboard')]:
        client.cookies.clear()
        signin(client, email)
        assert client.get(page).status_code == 200


def test_provider_technician_ticket_list_redirects(sandbox):
    client, Session = sandbox
    with Session() as db:
        seed_demo(db)
    signin(client, 'tecnico1@hospitalops.example')
    response = client.get('/tickets')
    assert response.status_code == 303 and response.headers['location'] == '/mis-tickets'
