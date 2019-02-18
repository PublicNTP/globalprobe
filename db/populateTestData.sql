DELETE FROM monitored_servers WHERE dns_name IN (
    'stratum2-01.bom01.publicntp.org',
    'stratum2-01.sin01.publicntp.org',
    'stratum2-01.gru01.publicntp.org'
);

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
    
