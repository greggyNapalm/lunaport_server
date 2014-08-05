#--data '{"fqdn":"aaaa.bbb.ccc"}' \
curl -v \
--user firebat_Ig7GvBeMxP:CEeerpoYju \
-X POST \
-H 'Content-Type: application/json' \
--data '{"name": "test_reduce", "kwargs": {"test_id": "28"}}' \
'http://lunaport.domain.ru/api/v1.0/job/'
