DROP INDEX IF EXISTS server_addresses_server_id_idx;
DROP INDEX IF EXISTS monitored_servers_owner_idx;
DROP TABLE IF EXISTS server_addresses;
DROP TABLE IF EXISTS monitored_servers;

CREATE TABLE monitored_servers (
    server_id               serial  PRIMARY KEY,
    owner_cognito_id        uuid    NOT NULL,
    dns_name                varchar NOT NULL,
    display_name            varchar,
    display_description     varchar,
    display_location        varchar,
    notes                   varchar
);

CREATE TABLE server_addresses (
    server_address_id       serial  PRIMARY KEY,
    server_id               int     REFERENCES monitored_servers(server_id) ON DELETE CASCADE NOT NULL,
    address                 inet    NOT NULL UNIQUE
);

CREATE INDEX monitored_servers_owner_idx        ON monitored_servers (owner_cognito_id);

CREATE INDEX server_addresses_server_id_idx     ON server_addresses (server_id);
