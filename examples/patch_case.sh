curl -v \
--user firebat_Ig7GvBeMxP:CEeerpoYju \
-X PATCH \
-H 'Content-Type: application/json' \
--data '{"notification": {"issue tracker": {"on_start": "true"}}, "oracle": {"fixture": "false"}, "name": "app-research", "descr": "research only. no alerts. no SLA1."}' \
'http://lunaport.domain.ru/api/v1.0/case/2'
