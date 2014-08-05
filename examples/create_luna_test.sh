#--data '{"fqdn":"aaaa.bbb.ccc"}' \
curl -v \
--user firebat_Ig7GvBeMxP:CEeerpoYju \
-X POST \
-H 'Content-Type: application/json' \
--data '{"env":"luna-tank-api", "case": "usr-napalm-dev", "luna_id":"155482", "t_tank_id":"617", "initiator":"firebat", "autocomplete": "true"}' \
'http://dev.lunaport.domain.ru/api/v1.0/tests/'
