#--data '{"fqdn":"aaaa.bbb.ccc"}' \
curl -v \
--user firebat_Ig7GvBeMxP:CEeerpoYju \
-X POST \
-H 'Content-Type: application/json' \
--data '{"case_name": "usr-napalm-dev", "user_login": "firebat", "cfg": {"on_start":"true"}}' \
'http://lunaport.domain.ru/api/v1.0/notifications/'
