from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


def now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Hospital(Base):
    __tablename__ = 'hospitals'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), unique=True)
    code: Mapped[str] = mapped_column(String(30), unique=True)
    tax_id: Mapped[str] = mapped_column(String(40), default='')
    address: Mapped[str] = mapped_column(String(250), default='')
    email: Mapped[str] = mapped_column(String(160), default='')
    phone: Mapped[str] = mapped_column(String(50), default='')
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    color: Mapped[str] = mapped_column(String(7), default='#2563eb')
    portal_name: Mapped[str] = mapped_column(String(90), default='Portal Hospitalario')
    tickets_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    inventory_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    crm_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Department(Base):
    __tablename__ = 'departments'
    __table_args__ = (UniqueConstraint('hospital_id', 'name'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    hospital_id: Mapped[int] = mapped_column(ForeignKey('hospitals.id'), index=True)
    name: Mapped[str] = mapped_column(String(120))


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    hospital_id: Mapped[int | None] = mapped_column(ForeignKey('hospitals.id'), index=True, nullable=True)
    department_id: Mapped[int | None] = mapped_column(ForeignKey('departments.id'), nullable=True)
    name: Mapped[str] = mapped_column(String(150))
    email: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(250))
    role: Mapped[str] = mapped_column(String(25), default='solicitante')
    job_title: Mapped[str] = mapped_column(String(120), default='')
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    approval: Mapped[str] = mapped_column(String(20), default='pending')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    hospital: Mapped[Hospital | None] = relationship()
    department: Mapped[Department | None] = relationship()


class Asset(Base):
    __tablename__ = 'assets'
    __table_args__ = (UniqueConstraint('hospital_id', 'code'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    hospital_id: Mapped[int] = mapped_column(ForeignKey('hospitals.id'), index=True)
    code: Mapped[str] = mapped_column(String(70))
    name: Mapped[str] = mapped_column(String(150))
    category: Mapped[str] = mapped_column(String(90), default='Equipamiento')
    location: Mapped[str] = mapped_column(String(150), default='')
    serial_number: Mapped[str] = mapped_column(String(100), default='')
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Ticket(Base):
    __tablename__ = 'tickets'
    id: Mapped[int] = mapped_column(primary_key=True)
    hospital_id: Mapped[int] = mapped_column(ForeignKey('hospitals.id'), index=True)
    requester_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    assignee_id: Mapped[int | None] = mapped_column(ForeignKey('users.id'), nullable=True)
    confirmed_by_id: Mapped[int | None] = mapped_column(ForeignKey('users.id'), nullable=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(90), default='Soporte')
    priority: Mapped[str] = mapped_column(String(20), default='media')
    status: Mapped[str] = mapped_column(String(25), default='pendiente')
    location: Mapped[str] = mapped_column(String(150), default='')
    asset_id: Mapped[int | None] = mapped_column(ForeignKey('assets.id'), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)
    hospital: Mapped[Hospital] = relationship()
    requester: Mapped[User] = relationship(foreign_keys=[requester_id])
    assignee: Mapped[User | None] = relationship(foreign_keys=[assignee_id])
    confirmer: Mapped[User | None] = relationship(foreign_keys=[confirmed_by_id])
    asset: Mapped[Asset | None] = relationship()


class TicketComment(Base):
    __tablename__ = 'ticket_comments'
    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey('tickets.id'), index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    body: Mapped[str] = mapped_column(Text)
    internal: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    author: Mapped[User] = relationship()


class InventoryItem(Base):
    __tablename__ = 'inventory_items'
    __table_args__ = (UniqueConstraint('hospital_id', 'sku'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    hospital_id: Mapped[int] = mapped_column(ForeignKey('hospitals.id'), index=True)
    sku: Mapped[str] = mapped_column(String(60))
    barcode: Mapped[str] = mapped_column(String(100), default='')
    name: Mapped[str] = mapped_column(String(160))
    category: Mapped[str] = mapped_column(String(100), default='General')
    location: Mapped[str] = mapped_column(String(150), default='Bodega')
    gross_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    sale_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    stock: Mapped[int] = mapped_column(Integer, default=0)
    min_stock: Mapped[int] = mapped_column(Integer, default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class InventoryMovement(Base):
    __tablename__ = 'inventory_movements'
    id: Mapped[int] = mapped_column(primary_key=True)
    hospital_id: Mapped[int] = mapped_column(ForeignKey('hospitals.id'), index=True)
    item_id: Mapped[int] = mapped_column(ForeignKey('inventory_items.id'))
    actor_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    ticket_id: Mapped[int | None] = mapped_column(ForeignKey('tickets.id'), nullable=True)
    kind: Mapped[str] = mapped_column(String(30))
    delta: Mapped[int] = mapped_column(Integer)
    resulting_stock: Mapped[int] = mapped_column(Integer)
    note: Mapped[str] = mapped_column(String(250))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    actor: Mapped[User] = relationship()
    item: Mapped[InventoryItem] = relationship()


class StockCount(Base):
    __tablename__ = 'stock_counts'
    id: Mapped[int] = mapped_column(primary_key=True)
    hospital_id: Mapped[int] = mapped_column(ForeignKey('hospitals.id'), index=True)
    created_by_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    status: Mapped[str] = mapped_column(String(20), default='abierto')
    note: Mapped[str] = mapped_column(String(200), default='')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[User] = relationship()


class StockCountLine(Base):
    __tablename__ = 'stock_count_lines'
    id: Mapped[int] = mapped_column(primary_key=True)
    stock_count_id: Mapped[int] = mapped_column(ForeignKey('stock_counts.id'), index=True)
    item_id: Mapped[int] = mapped_column(ForeignKey('inventory_items.id'))
    expected_stock: Mapped[int] = mapped_column(Integer)
    actual_stock: Mapped[int | None] = mapped_column(Integer, nullable=True)
    item: Mapped[InventoryItem] = relationship()


class CRMContact(Base):
    __tablename__ = 'crm_contacts'
    id: Mapped[int] = mapped_column(primary_key=True)
    hospital_id: Mapped[int] = mapped_column(ForeignKey('hospitals.id'), index=True)
    name: Mapped[str] = mapped_column(String(150))
    email: Mapped[str] = mapped_column(String(160), default='')
    phone: Mapped[str] = mapped_column(String(50), default='')
    job_title: Mapped[str] = mapped_column(String(150), default='')
    department: Mapped[str] = mapped_column(String(130), default='')
    notes: Mapped[str] = mapped_column(Text, default='')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class CRMOpportunity(Base):
    __tablename__ = 'crm_opportunities'
    id: Mapped[int] = mapped_column(primary_key=True)
    hospital_id: Mapped[int] = mapped_column(ForeignKey('hospitals.id'), index=True)
    contact_id: Mapped[int | None] = mapped_column(ForeignKey('crm_contacts.id'), nullable=True)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey('users.id'), nullable=True)
    name: Mapped[str] = mapped_column(String(190))
    value: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    stage: Mapped[str] = mapped_column(String(30), default='nuevo')
    expected_close: Mapped[str] = mapped_column(String(12), default='')
    notes: Mapped[str] = mapped_column(Text, default='')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    contact: Mapped[CRMContact | None] = relationship()
    owner: Mapped[User | None] = relationship()


class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id: Mapped[int] = mapped_column(primary_key=True)
    hospital_id: Mapped[int | None] = mapped_column(ForeignKey('hospitals.id'), nullable=True, index=True)
    actor_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    action: Mapped[str] = mapped_column(String(90))
    entity: Mapped[str] = mapped_column(String(90))
    entity_id: Mapped[int | None] = mapped_column(Integer)
    detail: Mapped[str] = mapped_column(String(250), default='')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    actor: Mapped[User] = relationship()


# Recursos de la empresa prestadora: no pertenecen a un hospital en particular.
class ProviderItem(Base):
    __tablename__ = 'provider_items'
    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160))
    category: Mapped[str] = mapped_column(String(100), default='General')
    location: Mapped[str] = mapped_column(String(120), default='Bodega central')
    gross_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    sale_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    stock: Mapped[int] = mapped_column(Integer, default=0)
    min_stock: Mapped[int] = mapped_column(Integer, default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class TechnicianStock(Base):
    __tablename__ = 'technician_stock'
    __table_args__ = (UniqueConstraint('item_id', 'technician_id'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey('provider_items.id'), index=True)
    technician_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    item: Mapped[ProviderItem] = relationship()
    technician: Mapped[User] = relationship()


class ProviderMovement(Base):
    __tablename__ = 'provider_movements'
    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey('provider_items.id'), index=True)
    technician_id: Mapped[int | None] = mapped_column(ForeignKey('users.id'), nullable=True)
    actor_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    ticket_id: Mapped[int | None] = mapped_column(ForeignKey('tickets.id'), nullable=True)
    hospital_id: Mapped[int | None] = mapped_column(ForeignKey('hospitals.id'), nullable=True)
    kind: Mapped[str] = mapped_column(String(30))
    quantity: Mapped[int] = mapped_column(Integer)
    note: Mapped[str] = mapped_column(String(250))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    item: Mapped[ProviderItem] = relationship()
    technician: Mapped[User | None] = relationship(foreign_keys=[technician_id])
    actor: Mapped[User] = relationship(foreign_keys=[actor_id])
    ticket: Mapped[Ticket | None] = relationship()


class LoginAttempt(Base):
    __tablename__ = 'login_attempts'
    id: Mapped[int] = mapped_column(primary_key=True)
    ip: Mapped[str] = mapped_column(String(48), index=True)
    email_digest: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now, index=True)


class SessionEpoch(Base):
    """Server-side revocation for otherwise signed-cookie sessions."""
    __tablename__ = 'session_epochs'
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), primary_key=True)
    epoch: Mapped[int] = mapped_column(Integer, default=1)
