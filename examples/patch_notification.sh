curl -v \
--user firebat_Ig7GvBeMxP:CEeerpoYju \
-X PATCH \
-H 'Content-Type: application/json' \
--data '{"case_name": "usr-napam-dev", "user_login": "firebat", "cfg": {"on_start":"false"}}' \
'http://dev.lunaport.domain.ru/api/v1.0/notifications/usr-napalm-dev/napalm'
