/*
    Lunaport Server database 0.0.1
    FIXME: add lnk to repo
    Dumped from database version 9.2.4
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Creates schema, default data values, grant permission.
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

--DO $$ BEGIN EXECUTE format('ALTER DATABASE %i SET timezone TO %i', current_database(), 'UTC'); END $$;

/* dc - Datacenter */
CREATE TABLE dc (
    id serial PRIMARY KEY,
    name character varying,
    symbol character varying UNIQUE
);

/* line - one of networks inside datacenter */
CREATE TABLE line (
    id serial PRIMARY KEY,
    name character varying NOT NULL,
    dc_id integer NOT NULL references dc (id)
);

/* permission */
CREATE TABLE permission (
    id serial PRIMARY KEY,
    descr character varying
);

/* server */
CREATE TABLE server (
    id serial PRIMARY KEY,
    fqdn character varying NOT NULL UNIQUE,
    disabled boolean DEFAULT 'False',
    added_at timestamp without time zone,
    descr character varying,
    ip_addr inet NOT NULL,
    line_id integer DEFAULT -1 references line (id),
    is_spec_tank boolean,
    is_tank boolean,
    host_serv integer
);

/*
    engine - low level testing tool(io engine or so)
*/
CREATE TABLE engine (
    id SERIAL PRIMARY KEY,
    name character varying NOT NULL UNIQUE,
    descr character varying
);

/* 
    environment - test running platform like: 3rd party framework, manually.
*/
CREATE TABLE environment (
    id SERIAL PRIMARY KEY,
    name character varying NOT NULL,
    descr character varying
);

/* user */
CREATE TABLE "user" (
    id SERIAL PRIMARY KEY,
    login character varying NOT NULL UNIQUE,
    first_name character varying NOT NULL,
    last_name character varying NOT NULL,
    settings json,
    email character varying NOT NULL,
    --password character varying,
    is_staff boolean NOT NULL,
    is_superuser boolean NOT NULL,
    is_robot boolean NOT NULL,
    last_login timestamp without time zone,
    date_joined timestamp without time zone DEFAULT NOW()
);

/* token - HTTP basic auth params to auth calls in REST API
   sault uniq for each token.
 */
CREATE TABLE token (
    id SERIAL PRIMARY KEY,
    name character varying NOT NULL,
    sault character varying NOT NULL,
    hash character varying NOT NULL, -- SHA1
    responsible_id integer references "user" (id),
    owner_id integer references "user" (id),
    permission_id integer references permission (id),
    descr character varying NOT NULL
);

/* case */
CREATE TABLE "case" (
    id SERIAL PRIMARY KEY,
    name character varying NOT NULL UNIQUE,
    descr character varying NOT NULL,
    oracle json DEFAULT '{"fixture": "false"}',
    --rule character varying DEFAULT 'always True',
    notification json DEFAULT NULL,
    --boolean DEFAULT False,
    added_at timestamp without time zone DEFAULT NOW(),
    changed_at timestamp without time zone DEFAULT NOW()
);

/* case_responsible m2m */
CREATE TABLE "case_responsible" (
    case_id integer references "case" (id),
    responsible_id integer references "user" (id),
    CONSTRAINT case_responsible_pkey PRIMARY KEY (case_id, responsible_id)
);

/* case_user_cc m2m */
CREATE TABLE "case_user_cc" (
    case_id integer references "case" (id),
    user_id integer references "user" (id),
    cfg json DEFAULT NULL,
    CONSTRAINT case_user_cc_pkey PRIMARY KEY (case_id, user_id)
);

/*
    test status - final state machine with such transitions allowed:
    pending -> failed, pending -> in_progress
    in_progress -> failed, in_progress -> done, done -> reducing
*/
CREATE TABLE "t_status" (
    id SERIAL PRIMARY KEY,
    name character varying NOT NULL UNIQUE,
    descr character varying
);

/* project - common for all trackers: JIRA, Startrack, Redmine, etc */
CREATE TABLE "project" (
    id SERIAL PRIMARY KEY,
    lead character varying,
    added_at timestamp without time zone DEFAULT NOW(),
    name character varying UNIQUE,
    descr character varying,
    provider character varying
);

/* issue - common for all trackers: JIRA, Startrack, Redmine, etc */
CREATE TABLE "issue" (
    id SERIAL PRIMARY KEY,
    added_at timestamp without time zone DEFAULT NOW(),
    name character varying UNIQUE,
    title character varying,
    descr character varying,
    reporter integer NOT NULL references "user" (id),
    assignee integer NOT NULL references "user" (id),
    closed boolean DEFAULT 'False',
    provider character varying,
    project_id integer NOT NULL references "project" (id)
);

/* ammo */
CREATE TABLE "ammo" (
    id SERIAL PRIMARY KEY,
    case_id integer references "case" (id) NOT NULL,
    owner_id integer NOT NULL references "user" (id),
    name character varying,
    descr character varying,
    path character varying DEFAULT NULL, /* NULL 1st phase of two phase commit*/
    added_at timestamp without time zone DEFAULT NOW(),
    last_used_at timestamp without time zone,
    hash character varying UNIQUE,
    meta json
);

/* test */
CREATE TABLE "test" (
    id SERIAL PRIMARY KEY,
    parent_id integer,
    t_status_id integer NOT NULL references "t_status" (id),
    resolution boolean DEFAULT NULL,
    case_id integer NOT NULL references "case" (id),
    ammo_id integer DEFAULT NULL references "ammo" (id),
    engine_id integer  NOT NULL references engine (id),
    environment_id integer NOT NULL references environment (id),
    initiator_id integer NOT NULL references "user" (id),
    name character varying,
    descr character varying,
    issue_id integer NOT NULL references "issue" (id),
    load_src_id integer NOT NULL references "server" (id),
    load_dst_id integer NOT NULL references "server" (id),
    added_at timestamp without time zone DEFAULT NOW(),
    started_at timestamp without time zone,
    finished_at timestamp without time zone,
    files json DEFAULT NULL,
    generator_cfg json DEFAULT NULL
);

/* evaluation */
CREATE TABLE "evaluation" (
    id SERIAL PRIMARY KEY,
    test_id integer references "test" (id),
    --case_id integer references "case" (id),
    oracle json,
    result json,
    passed boolean DEFAULT 'False',
    added_at timestamp without time zone DEFAULT NOW()
);

/* stat */
CREATE TABLE "stat" (
    --id SERIAL UNIQUE,
    test_id integer references "test" (id),
    ammo_tag character varying NOT NULL,
    version integer NOT NULL,
    doc json,
    added_at timestamp without time zone DEFAULT NOW(),
    PRIMARY KEY(test_id, ammo_tag),
    UNIQUE (test_id, ammo_tag)
);

/* chart */
CREATE TABLE "chart" (
    --id SERIAL UNIQUE,
    test_id integer references "test" (id),
    ammo_tag character varying NOT NULL,
    version integer NOT NULL,
    doc json,
    added_at timestamp without time zone DEFAULT NOW(),
    PRIMARY KEY(test_id, ammo_tag),
    UNIQUE (test_id, ammo_tag)
);

/* dc 
CREATE TABLE "dc" (
    id SERIAL PRIMARY KEY,
    name character varying UNIQUE NOT NULL
);

 line 
CREATE TABLE "line" (
    id integer PRIMARY KEY,
    name character varying UNIQUE NOT NULL,
    dc_id integer NOT NULL references "dc" (id)
);
*/

/* path */
CREATE TABLE "path" (
    from_host integer NOT NULL references "server" (id),
    to_host integer NOT NULL references "server" (id),
    num smallint,
    hops TEXT[],
    PRIMARY KEY(from_host, to_host)
);

/* hook */
CREATE TABLE "hook" (
    id serial PRIMARY KEY,
    name character varying UNIQUE NOT NULL,
    descr character varying NOT NULL,
    cfg_example json NOT NULL
);

/* hook_registration */
CREATE TABLE "hook_registration" (
    id serial PRIMARY KEY,
    is_enabled boolean DEFAULT 'False',
    descr character varying,
    case_id integer references "case" (id),
    hook_id integer references "hook" (id),
    cfg json,
    owner_id integer references "user" (id),
    added_at timestamp without time zone DEFAULT NOW(),
    last_used_at timestamp without time zone
);

/* initial data
   for fixtures used in unittesting :see test_data.sql
 */
insert into "permission" (descr) values
    ('ro - read only'),
    ('rwo - read and write'),
    ('rwd - read, write and delete');

insert into "user" (login, first_name, last_name, email, is_staff, is_superuser, is_robot, date_joined) values
    ('robocop', 'fix', 'fix', 'fix', False, False, True, now()),
    ('firebat', 'fix', 'fix', 'fix', False, False, True, now());

insert into "engine" (name, descr) values
    ('phantom', 'Yandex cretaed IO engine.'),
    ('jmeter', 'apache foundation load testing tool.');

insert into "environment" (name, descr) values
    ('luna-tank-api-force', '3rd party load testing service. New Test will be launched.'),
    ('luna-tank-api', '3rd party load testing service. Test exists.'),
    ('yandex-tank', 'End user run test by itself with console tools.');

insert into "case" (name, descr, oracle) values
    ('undef', 'service value not available to regular user.', '{"fixture": "true"}');

insert into project (name) values
    ('undef');

insert into "issue" (name, descr, reporter, assignee, project_id) values
    ('undef', 'service value.', 1, 2, 1);

insert into "t_status" (name, descr) values
    ('pending', 'Just launched'),
    ('in_progress', 'Successfully started and running'),
    ('failed', 'Interrupted.'),
    ('reducing', 'Aggregating test artifacts.'),
    ('done', 'Naturally finished.');

insert into "dc" (id, name) values
    (-1, 'no_such_dc');

insert into "line" (id, name, dc_id) values
    (-1, 'no_such_line', -1);

insert into "hook" (name, descr, cfg_example) values
    ('github', 'React on Git VCS push', '{"fixture": "true"}');


/* constraints */
ALTER TABLE "case" ADD root_test_id integer references "test" (id);
ALTER TABLE "case" ADD etalon_test_id integer references "test" (id);

/* access */
REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM lunaport;
GRANT ALL ON SCHEMA public TO lunaport;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO lunaport;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO lunaport;
-- EOF
