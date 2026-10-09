-- HospitalOps Comercial 1.1 · Esquema inicial PostgreSQL · REFERENCIA.
-- Para instalación nueva, la aplicación crea las tablas al arrancar.


CREATE TABLE hospitals (
	id SERIAL NOT NULL, 
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
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name), 
	UNIQUE (code)
)

;


CREATE TABLE login_attempts (
	id SERIAL NOT NULL, 
	ip VARCHAR(48) NOT NULL, 
	email_digest VARCHAR(64) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

;
CREATE INDEX ix_login_attempts_ip ON login_attempts (ip);
CREATE INDEX ix_login_attempts_created_at ON login_attempts (created_at);
CREATE INDEX ix_login_attempts_email_digest ON login_attempts (email_digest);


CREATE TABLE provider_items (
	id SERIAL NOT NULL, 
	sku VARCHAR(60) NOT NULL, 
	name VARCHAR(160) NOT NULL, 
	category VARCHAR(100) NOT NULL, 
	location VARCHAR(120) NOT NULL, 
	gross_cost NUMERIC(14, 2) NOT NULL, 
	sale_price NUMERIC(14, 2) NOT NULL, 
	stock INTEGER NOT NULL, 
	min_stock INTEGER NOT NULL, 
	active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

;
CREATE UNIQUE INDEX ix_provider_items_sku ON provider_items (sku);


CREATE TABLE assets (
	id SERIAL NOT NULL, 
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
CREATE INDEX ix_assets_hospital_id ON assets (hospital_id);


CREATE TABLE crm_contacts (
	id SERIAL NOT NULL, 
	hospital_id INTEGER NOT NULL, 
	name VARCHAR(150) NOT NULL, 
	email VARCHAR(160) NOT NULL, 
	phone VARCHAR(50) NOT NULL, 
	job_title VARCHAR(150) NOT NULL, 
	department VARCHAR(130) NOT NULL, 
	notes TEXT NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(hospital_id) REFERENCES hospitals (id)
)

;
CREATE INDEX ix_crm_contacts_hospital_id ON crm_contacts (hospital_id);


CREATE TABLE departments (
	id SERIAL NOT NULL, 
	hospital_id INTEGER NOT NULL, 
	name VARCHAR(120) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (hospital_id, name), 
	FOREIGN KEY(hospital_id) REFERENCES hospitals (id)
)

;
CREATE INDEX ix_departments_hospital_id ON departments (hospital_id);


CREATE TABLE inventory_items (
	id SERIAL NOT NULL, 
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
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (hospital_id, sku), 
	FOREIGN KEY(hospital_id) REFERENCES hospitals (id)
)

;
CREATE INDEX ix_inventory_items_hospital_id ON inventory_items (hospital_id);


CREATE TABLE users (
	id SERIAL NOT NULL, 
	hospital_id INTEGER, 
	department_id INTEGER, 
	name VARCHAR(150) NOT NULL, 
	email VARCHAR(160) NOT NULL, 
	password_hash VARCHAR(250) NOT NULL, 
	role VARCHAR(25) NOT NULL, 
	job_title VARCHAR(120) NOT NULL, 
	active BOOLEAN NOT NULL, 
	approval VARCHAR(20) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(hospital_id) REFERENCES hospitals (id), 
	FOREIGN KEY(department_id) REFERENCES departments (id)
)

;
CREATE UNIQUE INDEX ix_users_email ON users (email);
CREATE INDEX ix_users_hospital_id ON users (hospital_id);


CREATE TABLE audit_logs (
	id SERIAL NOT NULL, 
	hospital_id INTEGER, 
	actor_id INTEGER NOT NULL, 
	action VARCHAR(90) NOT NULL, 
	entity VARCHAR(90) NOT NULL, 
	entity_id INTEGER, 
	detail VARCHAR(250) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(hospital_id) REFERENCES hospitals (id), 
	FOREIGN KEY(actor_id) REFERENCES users (id)
)

;
CREATE INDEX ix_audit_logs_hospital_id ON audit_logs (hospital_id);


CREATE TABLE crm_opportunities (
	id SERIAL NOT NULL, 
	hospital_id INTEGER NOT NULL, 
	contact_id INTEGER, 
	owner_id INTEGER, 
	name VARCHAR(190) NOT NULL, 
	value NUMERIC(14, 2) NOT NULL, 
	stage VARCHAR(30) NOT NULL, 
	expected_close VARCHAR(12) NOT NULL, 
	notes TEXT NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(hospital_id) REFERENCES hospitals (id), 
	FOREIGN KEY(contact_id) REFERENCES crm_contacts (id), 
	FOREIGN KEY(owner_id) REFERENCES users (id)
)

;
CREATE INDEX ix_crm_opportunities_hospital_id ON crm_opportunities (hospital_id);


CREATE TABLE session_epochs (
	user_id INTEGER NOT NULL, 
	epoch INTEGER NOT NULL, 
	PRIMARY KEY (user_id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
)

;


CREATE TABLE stock_counts (
	id SERIAL NOT NULL, 
	hospital_id INTEGER NOT NULL, 
	created_by_id INTEGER NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	note VARCHAR(200) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	closed_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(hospital_id) REFERENCES hospitals (id), 
	FOREIGN KEY(created_by_id) REFERENCES users (id)
)

;
CREATE INDEX ix_stock_counts_hospital_id ON stock_counts (hospital_id);


CREATE TABLE technician_stock (
	id SERIAL NOT NULL, 
	item_id INTEGER NOT NULL, 
	technician_id INTEGER NOT NULL, 
	quantity INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (item_id, technician_id), 
	FOREIGN KEY(item_id) REFERENCES provider_items (id), 
	FOREIGN KEY(technician_id) REFERENCES users (id)
)

;
CREATE INDEX ix_technician_stock_item_id ON technician_stock (item_id);
CREATE INDEX ix_technician_stock_technician_id ON technician_stock (technician_id);


CREATE TABLE tickets (
	id SERIAL NOT NULL, 
	hospital_id INTEGER NOT NULL, 
	requester_id INTEGER NOT NULL, 
	assignee_id INTEGER, 
	confirmed_by_id INTEGER, 
	confirmed_at TIMESTAMP WITHOUT TIME ZONE, 
	title VARCHAR(200) NOT NULL, 
	description TEXT NOT NULL, 
	category VARCHAR(90) NOT NULL, 
	priority VARCHAR(20) NOT NULL, 
	status VARCHAR(25) NOT NULL, 
	location VARCHAR(150) NOT NULL, 
	asset_id INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(hospital_id) REFERENCES hospitals (id), 
	FOREIGN KEY(requester_id) REFERENCES users (id), 
	FOREIGN KEY(assignee_id) REFERENCES users (id), 
	FOREIGN KEY(confirmed_by_id) REFERENCES users (id), 
	FOREIGN KEY(asset_id) REFERENCES assets (id)
)

;
CREATE INDEX ix_tickets_hospital_id ON tickets (hospital_id);


CREATE TABLE inventory_movements (
	id SERIAL NOT NULL, 
	hospital_id INTEGER NOT NULL, 
	item_id INTEGER NOT NULL, 
	actor_id INTEGER NOT NULL, 
	ticket_id INTEGER, 
	kind VARCHAR(30) NOT NULL, 
	delta INTEGER NOT NULL, 
	resulting_stock INTEGER NOT NULL, 
	note VARCHAR(250) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(hospital_id) REFERENCES hospitals (id), 
	FOREIGN KEY(item_id) REFERENCES inventory_items (id), 
	FOREIGN KEY(actor_id) REFERENCES users (id), 
	FOREIGN KEY(ticket_id) REFERENCES tickets (id)
)

;
CREATE INDEX ix_inventory_movements_hospital_id ON inventory_movements (hospital_id);


CREATE TABLE provider_movements (
	id SERIAL NOT NULL, 
	item_id INTEGER NOT NULL, 
	technician_id INTEGER, 
	actor_id INTEGER NOT NULL, 
	ticket_id INTEGER, 
	hospital_id INTEGER, 
	kind VARCHAR(30) NOT NULL, 
	quantity INTEGER NOT NULL, 
	note VARCHAR(250) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(item_id) REFERENCES provider_items (id), 
	FOREIGN KEY(technician_id) REFERENCES users (id), 
	FOREIGN KEY(actor_id) REFERENCES users (id), 
	FOREIGN KEY(ticket_id) REFERENCES tickets (id), 
	FOREIGN KEY(hospital_id) REFERENCES hospitals (id)
)

;
CREATE INDEX ix_provider_movements_item_id ON provider_movements (item_id);


CREATE TABLE stock_count_lines (
	id SERIAL NOT NULL, 
	stock_count_id INTEGER NOT NULL, 
	item_id INTEGER NOT NULL, 
	expected_stock INTEGER NOT NULL, 
	actual_stock INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(stock_count_id) REFERENCES stock_counts (id), 
	FOREIGN KEY(item_id) REFERENCES inventory_items (id)
)

;
CREATE INDEX ix_stock_count_lines_stock_count_id ON stock_count_lines (stock_count_id);


CREATE TABLE ticket_comments (
	id SERIAL NOT NULL, 
	ticket_id INTEGER NOT NULL, 
	author_id INTEGER NOT NULL, 
	body TEXT NOT NULL, 
	internal BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(ticket_id) REFERENCES tickets (id), 
	FOREIGN KEY(author_id) REFERENCES users (id)
)

;
CREATE INDEX ix_ticket_comments_ticket_id ON ticket_comments (ticket_id);
