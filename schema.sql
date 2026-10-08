-- HospitalOps / SQL de referencia compatible con SQLite
-- Para PostgreSQL, usar los modelos SQLAlchemy o migraciones en lugar de este DDL.


CREATE TABLE hospitals (
	id INTEGER NOT NULL, 
	name VARCHAR(160) NOT NULL, 
	code VARCHAR(30) NOT NULL, 
	tax_id VARCHAR(40) NOT NULL, 
	address VARCHAR(250) NOT NULL, 
	email VARCHAR(160) NOT NULL, 
	phone VARCHAR(50) NOT NULL, 
	active BOOLEAN NOT NULL, 
	color VARCHAR(7) NOT NULL, 
	portal_name VARCHAR(90) NOT NULL, 
	tickets_enabled BOOLEAN NOT NULL, 
	inventory_enabled BOOLEAN NOT NULL, 
	crm_enabled BOOLEAN NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name), 
	UNIQUE (code)
)

;


CREATE TABLE assets (
	id INTEGER NOT NULL, 
	hospital_id INTEGER NOT NULL, 
	code VARCHAR(70) NOT NULL, 
	name VARCHAR(150) NOT NULL, 
	category VARCHAR(90) NOT NULL, 
	location VARCHAR(150) NOT NULL, 
	serial_number VARCHAR(100) NOT NULL, 
	active BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (hospital_id, code), 
	FOREIGN KEY(hospital_id) REFERENCES hospitals (id)
)

;


CREATE TABLE crm_contacts (
	id INTEGER NOT NULL, 
	hospital_id INTEGER NOT NULL, 
	name VARCHAR(150) NOT NULL, 
	email VARCHAR(160) NOT NULL, 
	phone VARCHAR(50) NOT NULL, 
	job_title VARCHAR(150) NOT NULL, 
	department VARCHAR(130) NOT NULL, 
	notes TEXT NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(hospital_id) REFERENCES hospitals (id)
)

;


CREATE TABLE departments (
	id INTEGER NOT NULL, 
	hospital_id INTEGER NOT NULL, 
	name VARCHAR(120) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (hospital_id, name), 
	FOREIGN KEY(hospital_id) REFERENCES hospitals (id)
)

;


CREATE TABLE inventory_items (
	id INTEGER NOT NULL, 
	hospital_id INTEGER NOT NULL, 
	sku VARCHAR(60) NOT NULL, 
	barcode VARCHAR(100) NOT NULL, 
	name VARCHAR(160) NOT NULL, 
	category VARCHAR(100) NOT NULL, 
	location VARCHAR(150) NOT NULL, 
	gross_cost NUMERIC(14, 2) NOT NULL, 
	sale_price NUMERIC(14, 2) NOT NULL, 
	stock INTEGER NOT NULL, 
	min_stock INTEGER NOT NULL, 
	active BOOLEAN NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (hospital_id, sku), 
	FOREIGN KEY(hospital_id) REFERENCES hospitals (id)
)

;


CREATE TABLE users (
	id INTEGER NOT NULL, 
	hospital_id INTEGER, 
	department_id INTEGER, 
	name VARCHAR(150) NOT NULL, 
	email VARCHAR(160) NOT NULL, 
	password_hash VARCHAR(250) NOT NULL, 
	role VARCHAR(25) NOT NULL, 
	job_title VARCHAR(120) NOT NULL, 
	active BOOLEAN NOT NULL, 
	approval VARCHAR(20) NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(hospital_id) REFERENCES hospitals (id), 
	FOREIGN KEY(department_id) REFERENCES departments (id)
)

;


CREATE TABLE audit_logs (
	id INTEGER NOT NULL, 
	hospital_id INTEGER, 
	actor_id INTEGER NOT NULL, 
	action VARCHAR(90) NOT NULL, 
	entity VARCHAR(90) NOT NULL, 
	entity_id INTEGER, 
	detail VARCHAR(250) NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(hospital_id) REFERENCES hospitals (id), 
	FOREIGN KEY(actor_id) REFERENCES users (id)
)

;


CREATE TABLE crm_opportunities (
	id INTEGER NOT NULL, 
	hospital_id INTEGER NOT NULL, 
	contact_id INTEGER, 
	owner_id INTEGER, 
	name VARCHAR(190) NOT NULL, 
	value NUMERIC(14, 2) NOT NULL, 
	stage VARCHAR(30) NOT NULL, 
	expected_close VARCHAR(12) NOT NULL, 
	notes TEXT NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(hospital_id) REFERENCES hospitals (id), 
	FOREIGN KEY(contact_id) REFERENCES crm_contacts (id), 
	FOREIGN KEY(owner_id) REFERENCES users (id)
)

;


CREATE TABLE stock_counts (
	id INTEGER NOT NULL, 
	hospital_id INTEGER NOT NULL, 
	created_by_id INTEGER NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	note VARCHAR(200) NOT NULL, 
	created_at DATETIME NOT NULL, 
	closed_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(hospital_id) REFERENCES hospitals (id), 
	FOREIGN KEY(created_by_id) REFERENCES users (id)
)

;


CREATE TABLE tickets (
	id INTEGER NOT NULL, 
	hospital_id INTEGER NOT NULL, 
	requester_id INTEGER NOT NULL, 
	assignee_id INTEGER, 
	confirmed_by_id INTEGER, 
	confirmed_at DATETIME, 
	title VARCHAR(200) NOT NULL, 
	description TEXT NOT NULL, 
	category VARCHAR(90) NOT NULL, 
	priority VARCHAR(20) NOT NULL, 
	status VARCHAR(25) NOT NULL, 
	location VARCHAR(150) NOT NULL, 
	asset_id INTEGER, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(hospital_id) REFERENCES hospitals (id), 
	FOREIGN KEY(requester_id) REFERENCES users (id), 
	FOREIGN KEY(assignee_id) REFERENCES users (id), 
	FOREIGN KEY(confirmed_by_id) REFERENCES users (id), 
	FOREIGN KEY(asset_id) REFERENCES assets (id)
)

;


CREATE TABLE inventory_movements (
	id INTEGER NOT NULL, 
	hospital_id INTEGER NOT NULL, 
	item_id INTEGER NOT NULL, 
	actor_id INTEGER NOT NULL, 
	ticket_id INTEGER, 
	kind VARCHAR(30) NOT NULL, 
	delta INTEGER NOT NULL, 
	resulting_stock INTEGER NOT NULL, 
	note VARCHAR(250) NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(hospital_id) REFERENCES hospitals (id), 
	FOREIGN KEY(item_id) REFERENCES inventory_items (id), 
	FOREIGN KEY(actor_id) REFERENCES users (id), 
	FOREIGN KEY(ticket_id) REFERENCES tickets (id)
)

;


CREATE TABLE stock_count_lines (
	id INTEGER NOT NULL, 
	stock_count_id INTEGER NOT NULL, 
	item_id INTEGER NOT NULL, 
	expected_stock INTEGER NOT NULL, 
	actual_stock INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(stock_count_id) REFERENCES stock_counts (id), 
	FOREIGN KEY(item_id) REFERENCES inventory_items (id)
)

;


CREATE TABLE ticket_comments (
	id INTEGER NOT NULL, 
	ticket_id INTEGER NOT NULL, 
	author_id INTEGER NOT NULL, 
	body TEXT NOT NULL, 
	internal BOOLEAN NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(ticket_id) REFERENCES tickets (id), 
	FOREIGN KEY(author_id) REFERENCES users (id)
)

;

CREATE INDEX ix_assets_hospital_id ON assets (hospital_id);
CREATE INDEX ix_crm_contacts_hospital_id ON crm_contacts (hospital_id);
CREATE INDEX ix_departments_hospital_id ON departments (hospital_id);
CREATE INDEX ix_inventory_items_hospital_id ON inventory_items (hospital_id);
CREATE UNIQUE INDEX ix_users_email ON users (email);
CREATE INDEX ix_users_hospital_id ON users (hospital_id);
CREATE INDEX ix_audit_logs_hospital_id ON audit_logs (hospital_id);
CREATE INDEX ix_crm_opportunities_hospital_id ON crm_opportunities (hospital_id);
CREATE INDEX ix_stock_counts_hospital_id ON stock_counts (hospital_id);
CREATE INDEX ix_tickets_hospital_id ON tickets (hospital_id);
CREATE INDEX ix_inventory_movements_hospital_id ON inventory_movements (hospital_id);
CREATE INDEX ix_stock_count_lines_stock_count_id ON stock_count_lines (stock_count_id);
CREATE INDEX ix_ticket_comments_ticket_id ON ticket_comments (ticket_id);
