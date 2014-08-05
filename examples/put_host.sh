curl -v \
--user napalm_IZD5VL1EcLc2lTp:Ge53gsRSs0gej9o \
-X PUT \
-H 'Content-Type: application/json' \
--data '{"is_spec_tank": false, "is_tank": true, "fqdn": "generator.domain.org"}' \
'http://dev.lunaport.domain.ru/api/v1.0/host/'
