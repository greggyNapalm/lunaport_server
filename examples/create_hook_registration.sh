curl -v \
--user napalm_LCcj95RMJoOwilP:aG7GkJEVrJ1vvZj \
-X POST \
-H 'Content-Type: application/json' \
--data '{"case_id": 14, "hook_id": 1, "descr": "aAa debug debug.", "cfg": {"other": "stuff"}}' \
'http://dev.lunaport.domain.ru/api/v1.0/hooks/registration/'
