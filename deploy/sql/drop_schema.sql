/*
    Lunaport Server database. 
    FIXME: add lnk to repo
    Dumped from database version 9.2.4
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Removes all data from lunaport db, recreate schema.
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

DROP SCHEMA public CASCADE; CREATE SCHEMA public AUTHORIZATION lunaport; GRANT ALL ON SCHEMA public TO lunaport;
-- EOF
