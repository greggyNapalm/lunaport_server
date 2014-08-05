curl -v \
--user firebat_Ig7GvBeMxP:CEeerpoYju \
-X POST \
-H 'Content-Type: application/json' \
--data '{"oracle": {"fixture": "true"}, "name": "app-relese", "descr": "Pre-relise acceptance test for app."}' \
'http://lunaport.domain.ru/api/v1.0/case/'
