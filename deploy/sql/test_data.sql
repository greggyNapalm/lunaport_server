/*
    Lunaport Server database.
    FIXME: add lnk to repo
    Dumped from database version 9.2.4
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Fill database with sample data to run test and to start develop.
*/

SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


SET search_path = public, pg_catalog;
SET default_tablespace = '';
SET default_with_oids = false;

/* initial data */
insert into "token" (name, sault, hash, responsible_id, owner_id, permission_id, descr) values
    ('firebat_AAA', 'BBB', 'CCC', 1, 2, 3, 'Development only. Provisioned by deploy script.');
--insert into "token" (value, responsible_id, permission_id, description) values
--    ('valera', 2, 3, 'Development only. Provisioned by deploy script.');

insert into "case" (name, descr, oracle) values
    ('usr-napalm-dev', 'Testing/Development only. Provisioned by deploy script. #1', '[{"kw": {"tag": "all"}, "name": "assert_resp_times_distr", "arg": [99, "<=", 200]}, {"kw": {}, "name": "assert_errno_distr", "arg": [0, ">", 99]}, {"kw": {}, "name": "assert_http_status_distr", "arg": [200, ">", 99]}, {"kw": {}, "name": "assert_phantom_exec_fract", "arg": ["<", 0.1]}, {"kw": {}, "name": "assert_rtt_fract", "arg": ["connecting", ">=", 15]}]'),
    ('rabota-wizzard', 'Testing/Development only. Provisioned by deploy script. #2', '{"two": "y"}'),
    ('auto-front', 'Testing/Development only. Provisioned by deploy script. #3', '{"three": "z"}');



insert into "dc" (id, name) values
    (1, 'spb'),
    (2, 'msk');


insert into "line" (id, name, dc_id) values
    (11, 'spb1', 1),
    (22, 'spb2', 1),
    (33, 'msk', 2);

insert into server (fqdn, added_at, ip_addr) values
    ('fobos.generator.org', now(), '1.1.1.1'),
    ('deimos.generator.org', now(), '2.2.2.2');
    ('app.target.org', now(), '3.3.3.3');

insert into project (name, descr, provider) values
    ('conquest', '4 debugging and testing', 'jira'),
    ('domination', 'enslaving the world', 'jira'),
    ('communism', 'и Ленин такой молодой и юный октябрь впереди', 'jira');

insert into issue (name, reporter, assignee, project_id) values
    ('conquest-111', 1, 2, 1),
    ('domination-222', 1, 2, 2),
    ('communism-333', 2, 1, 3);

INSERT INTO test
            (t_status_id,
             case_id,
             parent_id,
             engine_id,
             environment_id,
             lunapark_id,
             lunapark,
             initiator_id,
             "name",
             descr,
             issue_id,
             load_src_id,
             load_dst_id,
             started_at,
             finished_at,
             files,
             generator_cfg)
VALUES      ( (SELECT id FROM t_status WHERE  name = 'pending'),
              (SELECT id FROM "case" WHERE  name = 'usr-napalm-dev'),
              (SELECT 155),
              (SELECT id FROM engine WHERE name = 'phantom'),
              (SELECT id FROM environment WHERE name = 'yandex-tank'),
              NULL,
              'null',
              (SELECT id FROM "user" WHERE  login = 'firebat'),
              'this is a test name',
              'this is a descr',
              (SELECT id FROM "issue" WHERE name = 'conquest-111'),
              (SELECT id FROM server WHERE  fqdn = 'fobos.generator.org'),
              (SELECT id FROM server WHERE  fqdn = 'app.target.org'),
              NULL,
              NULL,
              NULL,
              NULL),
            ( (SELECT id FROM t_status WHERE  name = 'done'),
              (SELECT id FROM "case" WHERE  name = 'usr-napalm-dev'),
              (SELECT 1),
              (SELECT id FROM engine WHERE name = 'phantom'),
              (SELECT id FROM environment WHERE name = 'yandex-tank'),
              NULL,
              'null',
              (SELECT id FROM "user" WHERE  login = 'firebat'),
              'rabota test issue #2',
              'Robots do not sweat',
              (SELECT id FROM "issue" WHERE name = 'domination-222'),
              (SELECT id FROM server WHERE  fqdn = 'deimos.generator.org'),
              (SELECT id FROM server WHERE  fqdn = 'app.target.org'),
              NULL,
              NULL,
              NULL,
              NULL),
            ( (SELECT id FROM t_status WHERE  name = 'in_progress'),
              (SELECT id FROM "case" WHERE  name = 'usr-napalm-dev'),
              (SELECT 1),
              (SELECT id FROM engine WHERE name = 'phantom'),
              (SELECT id FROM environment WHERE name = 'yandex-tank'),
              NULL,
              'null',
              (SELECT id FROM "user" WHERE  login = 'firebat'),
              'rabota test issue #2',
              'Robots do not sweat',
              (SELECT id FROM "issue" WHERE name = 'communism-333'),
              (SELECT id FROM server WHERE  fqdn = 'fobos.generator.org'),
              (SELECT id FROM server WHERE  fqdn = 'app.target.org'),
              NULL,
              NULL,
              NULL,
              NULL)

-- EOF
