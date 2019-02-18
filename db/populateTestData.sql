DELETE FROM monitored_servers; 

INSERT INTO monitored_servers (owner_cognito_id, dns_name ) VALUES  
    ('3665f15f-36d8-42d4-b531-aa9284126bfe', 'stratum2-01.bom01.publicntp.org' ),
    ('3665f15f-36d8-42d4-b531-aa9284126bfe', 'stratum2-01.sin01.publicntp.org' ),
    ('3665f15f-36d8-42d4-b531-aa9284126bfe', 'stratum2-01.gru01.publicntp.org' );

INSERT INTO server_addresses (server_id, address) VALUES 
    ( (SELECT server_id FROM monitored_servers WHERE dns_name='stratum2-01.bom01.publicntp.org'),
        '52.66.76.135' ),
    ( (SELECT server_id FROM monitored_servers WHERE dns_name='stratum2-01.bom01.publicntp.org'),
        '2406:da1a:200:7201:d9ea:9ac5:32e3:339c' ),


    ( (SELECT server_id FROM monitored_servers WHERE dns_name='stratum2-01.sin01.publicntp.org'),
        '2406:da18:abd:d700:4fef:14aa:9534:95db'),


    ( (SELECT server_id FROM monitored_servers WHERE dns_name='stratum2-01.gru01.publicntp.org'),
        '54.233.172.242' ),

    ( (SELECT server_id FROM monitored_servers WHERE dns_name='stratum2-01.gru01.publicntp.org'),
        '2600:1f1e:5bb:8800:91e8:bd0:2121:3eb3' );


DELETE FROM probe_sites;
INSERT INTO probe_sites (site_location_id) VALUES 
    ( 'pdx01' ),
    ( 'iad01' ),
    ( 'gru01' ),
    ( 'fra01' ),
    ( 'bom01' ),
    ( 'sin01' ),
    ( 'inc01' ),
    ( 'syd01' );
    

INSERT INTO service_probes (probe_site_id, server_address, time_request_sent, time_response_received, round_trip_time, estimated_utc_offset)
VALUES 
    ( 
        (SELECT probe_site_id FROM probe_sites WHERE site_location_id = 'pdx01' ),
        (SELECT server_address_id FROM server_addresses WHERE address = '52.66.76.135' ),
        '2019-01-01 01:02:03.123456+00', 
        '2019-01-01 01:02:03.456789+00',
        (SELECT timestamp '2019-01-01 01:02:03.456789+00' - timestamp '2019-01-01 01:02:03.123456+00'),
        '0.007 seconds' 
    ),

    (
        (SELECT probe_site_id FROM probe_sites WHERE site_location_id = 'iad01' ),
        (SELECT server_address_id FROM server_addresses WHERE address = '52.66.76.135' ),
        '2019-01-01 01:02:09.123456+00',
        '2019-01-01 01:02:10.456789+00',
        (SELECT timestamp '2019-01-01 01:02:10.456789+00' - timestamp '2019-01-01 01:02:09.123456+00'),
        '0.013 seconds'
    ),

    (
        (SELECT probe_site_id FROM probe_sites WHERE site_location_id = 'gru01' ),
        (SELECT server_address_id FROM server_addresses WHERE address = '2406:da1a:200:7201:d9ea:9ac5:32e3:339c' ),
        '2019-01-02 03:05:09.123456+00',
        null,
        null,
        null
    ),

    (
        (SELECT probe_site_id FROM probe_sites WHERE site_location_id = 'fra01' ),
        (SELECT server_address_id FROM server_addresses WHERE address = '2406:da18:abd:d700:4fef:14aa:9534:95db'),
        '2019-01-15 05:15:09.123456+00',
        '2019-01-15 05:15:10.456789+00',
        (SELECT timestamp '2019-01-15 05:15:10.456789+00' - timestamp '2019-01-15 05:15:09.123456+00'),
        '0.147 seconds'
    )

;
