DROP INDEX IF EXISTS service_probes_utc_offset_idx;
DROP INDEX IF EXISTS service_probes_response_received_idx
DROP INDEX IF EXISTS service_probes_server_address_time_sent_idx;
DROP INDEX IF EXISTS server_addresses_server_id_idx;
DROP INDEX IF EXISTS monitored_servers_dns_name_idx;
DROP INDEX IF EXISTS monitored_servers_owner_idx;

DROP VIEW IF EXISTS sorted_utc_offsets;
DROP VIEW IF EXISTS unanswered_probes;

DROP TABLE IF EXISTS service_probes;
DROP TABLE IF EXISTS probe_sites;
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

CREATE TABLE probe_sites (
    probe_site_id           serial                      PRIMARY KEY,
    site_location_id        varchar                     NOT NULL UNIQUE
);

CREATE TABLE service_probes (
    probe_attempt_id        bigserial                   PRIMARY KEY,
    probe_site_id           integer                     REFERENCES probe_sites (probe_site_id) ON DELETE CASCADE NOT NULL,
    server_address          bigint                      REFERENCES server_addresses (server_address_id) ON DELETE CASCADE NOT NULL,
    time_request_sent       timestamp with time zone    NOT NULL,
    time_response_received  timestamp with time zone,
    round_trip_time         interval,
    estimated_utc_offset    interval
);

CREATE VIEW unanswered_probes AS
SELECT owner_cognito_id AS server_owner, site_location_id AS probe_site, dns_name, address, time_request_sent
FROM monitored_servers 
JOIN server_addresses ON monitored_servers.server_id = server_addresses.server_id 
JOIN service_probes ON server_addresses.server_address_id = service_probes.server_address 
JOIN probe_sites ON service_probes.probe_site_id = probe_sites.probe_site_id
WHERE time_response_received IS NULL 
ORDER BY owner_cognito_id, dns_name, time_request_sent, address;

CREATE VIEW sorted_utc_offsets AS
SELECT owner_cognito_id AS server_owner, site_location_id AS probe_site, dns_name, address, time_request_sent, estimated_utc_offset
FROM monitored_servers
JOIN server_addresses ON monitored_servers.server_id = server_addresses.server_id
JOIN service_probes ON server_addresses.server_address_id = service_probes.server_address
JOIN probe_sites ON service_probes.probe_site_id = probe_sites.probe_site_id
ORDER BY owner_cognito_id, abs(estimated_utc_offset), dns_name, address, time_request_sent;

CREATE VIEW probe_history AS
SELECT dns_name, address, time_request_sent, probe_site_id, time_response_received, round_trip_time, estimated_utc_offset
FROM monitored_servers
JOIN server_addresses
ON monitored_servers.server_id = server_addresses.server_id
JOIN service_probes
ON server_addresses.server_address_id = service_probes.server_address
WHERE owner_cognito_id = '3665f15f-36d8-42d4-b531-aa9284126bfe'
AND NOW() - time_request_sent <= interval '8640000 seconds'
AND address='52.66.76.135'
ORDER BY dns_name, address, time_request_sent, probe_site_id;

CREATE VIEW latest_probe_time AS
SELECT probe_site_id, MAX(time_Request_sent) 
FROM service_probes 
GROUP BY probe_site_id 
ORDER BY probe_site_id;

CREATE VIEW most_recent_probes AS
SELECT time_request_sent, site_location_id AS probe_site, dns_name, address,
    EXTRACT(microseconds FROM estimated_utc_offset)/1000000 AS utc_offset,
    EXTRACT(microseconds FROM round_trip_time)/1000000 as round_trip
FROM monitored_servers
JOIN server_addresses
ON monitored_servers.server_id = server_addresses.server_id
JOIN service_probes
ON server_addresses.server_address_id = service_probes.server_address
JOIN probe_sites
ON service_probes.probe_site_id = probe_sites.probe_site_id
ORDER BY time_request_sent DESC
LIMIT 20;




CREATE INDEX monitored_servers_owner_idx                    ON monitored_servers (owner_cognito_id);
CREATE INDEX monitored_servers_dns_name_idx                 ON monitored_servers (dns_name);

CREATE INDEX server_addresses_server_id_idx                 ON server_addresses (server_id);
CREATE INDEX server_addresses_address_idx                   ON server_addresses (address);

CREATE INDEX probe_sites_location_idx                       ON probe_sites (site_location_id);

CREATE INDEX service_probes_server_address_time_sent_idx    ON service_probes (server_address, time_request_sent);
CREATE INDEX service_probes_response_received_idx           ON service_probes (time_response_received);
CREATE INDEX service_probes_utc_offset_idx                  ON service_probes (server_address, estimated_utc_offset);
