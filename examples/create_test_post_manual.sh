curl -v \
--user firebat_Ig7GvBeMxP:CEeerpoYju \
-F "load_cfg=@feuer.ini" \
-F "phout=@phout.log" \
-F "load_src=generator.domain.org" \
-F "parent_id=155" \
-F "env=yandex-tank" \
-F "case=usr-napalm-dev" \
-F "initiator=firebat" \
'http://lunaport.domain.org/api/v1.0/tests/?token=valera'
