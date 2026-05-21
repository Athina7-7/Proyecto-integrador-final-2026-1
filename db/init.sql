CREATE TABLE IF NOT EXISTS registrations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    commune VARCHAR(20) NOT NULL,
    program VARCHAR(50) NOT NULL,
    language VARCHAR(20) NOT NULL,
    entry_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    served_by VARCHAR(50),
    client_ip VARCHAR(80)
);

CREATE INDEX IF NOT EXISTS idx_registrations_commune
    ON registrations (commune);

CREATE INDEX IF NOT EXISTS idx_registrations_program
    ON registrations (program);

CREATE INDEX IF NOT EXISTS idx_registrations_entry_at
    ON registrations (entry_at);
