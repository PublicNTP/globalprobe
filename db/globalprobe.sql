DROP INDEX IF EXISTS address_probe_attempts_time_sent_idx;
DROP INDEX IF EXISTS address_probe_attempts_probe_id;
DROP INDEX IF EXISTS address_probes_server_address_idx;
DROP INDEX IF EXISTS server_addresses_server_id_idx;
DROP INDEX IF EXISTS monitored_servers_owner_idx;

DROP TABLE IF EXISTS address_probe_attempts;
DROP TABLE IF EXISTS address_probes;
DROP TABLE IF EXISTS server_addresses;
DROP TABLE IF EXISTS monitored_servers;

CREATE TABLE monitored_servers (
    server_id               bigserial                   PRIMARY KEY,
    owner_cognito_id        uuid                        NOT NULL,
    dns_name                varchar                     NOT NULL UNIQUE,
    display_name            varchar,
    display_description     varchar,
    display_location        varchar,
    notes                   varchar
);

CREATE TABLE server_addresses (
    server_address_id       bigserial                   PRIMARY KEY,
    server_id               bigint                      REFERENCES monitored_servers(server_id) ON DELETE CASCADE NOT NULL,
    address                 inet                        NOT NULL UNIQUE
);

CREATE TABLE address_probes (
    probe_id                bigserial                   PRIMARY KEY,
    server_address          bigint                      REFERENCES server_addresses ON DELETE CASCADE NOT NULL 
);

CREATE TABLE address_probe_attempts (
    probe_attempt_id        bigserial                   PRIMARY KEY,
    probe_id                bigint                      REFERENCES address_probes (probe_id) ON DELETE CASCADE NOT NULL,
    attempt_number          integer                     NOT NULL,
    time_request_sent       timestamp with time zone    NOT NULL,
    time_response_received  timestamp with time zone,
    estimated_utc_offset    interval
);



CREATE INDEX monitored_servers_owner_idx                ON monitored_servers (owner_cognito_id);
CREATE INDEX monitored_servers_dns_name_idx             ON monitored_servers (dns_name);

CREATE INDEX server_addresses_server_id_idx             ON server_addresses (server_id);

CREATE INDEX address_probes_server_address_idx          ON address_probes (server_address);

CREATE INDEX address_probe_attempts_probe_id            ON address_probe_attempts (probe_id);

CREATE INDEX address_probe_attempts_time_sent_idx       ON address_probe_attempts (probe_id, time_request_sent);
