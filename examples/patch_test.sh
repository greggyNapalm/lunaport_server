#reducing
curl -v \
--user firebat_Ig7GvBeMxP:CEeerpoYju \
-X PATCH \
-H 'Content-Type: application/json' \
--data '{"status":"done", "finished_at": "2013-09-06T06:55:08+00:00", "resolution":false}' \
'http://lunaport.domain.ru/api/v1.0/tests/1'
