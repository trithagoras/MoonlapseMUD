--
-- PostgreSQL database cluster dump
--

SET default_transaction_read_only = off;

SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;

--
-- Roles
--

CREATE ROLE "MoonlapseAdmin";
ALTER ROLE "MoonlapseAdmin" WITH SUPERUSER INHERIT CREATEROLE CREATEDB LOGIN NOREPLICATION NOBYPASSRLS PASSWORD 'md5a052b8f587448c70ec0d342768608211';
CREATE ROLE "MoonlapseUser";
ALTER ROLE "MoonlapseUser" WITH NOSUPERUSER NOINHERIT NOCREATEROLE NOCREATEDB LOGIN NOREPLICATION NOBYPASSRLS PASSWORD 'md58d817c8d485fbdf699fd5243c026afb1' VALID UNTIL 'infinity';
CREATE ROLE pgloader_pg;
ALTER ROLE pgloader_pg WITH SUPERUSER INHERIT CREATEROLE CREATEDB LOGIN NOREPLICATION NOBYPASSRLS PASSWORD 'md5f1db81a37e60cc453f8c1b3eb0697c0e';
CREATE ROLE postgres;
ALTER ROLE postgres WITH SUPERUSER INHERIT CREATEROLE CREATEDB LOGIN REPLICATION BYPASSRLS;


--
-- Role memberships
--

GRANT "MoonlapseAdmin" TO "MoonlapseUser" GRANTED BY "MoonlapseAdmin";
GRANT pg_execute_server_program TO "MoonlapseUser" GRANTED BY "MoonlapseAdmin";
GRANT pg_monitor TO "MoonlapseUser" GRANTED BY "MoonlapseAdmin";
GRANT pg_read_all_settings TO "MoonlapseUser" GRANTED BY "MoonlapseAdmin";
GRANT pg_read_all_stats TO "MoonlapseUser" GRANTED BY "MoonlapseAdmin";
GRANT pg_read_server_files TO "MoonlapseUser" GRANTED BY "MoonlapseAdmin";
GRANT pg_signal_backend TO "MoonlapseUser" GRANTED BY "MoonlapseAdmin";
GRANT pg_stat_scan_tables TO "MoonlapseUser" GRANTED BY "MoonlapseAdmin";
GRANT pg_write_server_files TO "MoonlapseUser" GRANTED BY "MoonlapseAdmin";
GRANT pgloader_pg TO "MoonlapseUser" GRANTED BY "MoonlapseAdmin";
GRANT postgres TO "MoonlapseUser" GRANTED BY "MoonlapseAdmin";




--
-- Databases
--

--
-- Database "template1" dump
--

\connect template1

--
-- PostgreSQL database dump
--

-- Dumped from database version 12.3 (Ubuntu 12.3-1.pgdg18.04+1)
-- Dumped by pg_dump version 12.3 (Ubuntu 12.3-1.pgdg18.04+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- PostgreSQL database dump complete
--

--
-- Database "Moonlapse" dump
--

--
-- PostgreSQL database dump
--

-- Dumped from database version 12.3 (Ubuntu 12.3-1.pgdg18.04+1)
-- Dumped by pg_dump version 12.3 (Ubuntu 12.3-1.pgdg18.04+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: Moonlapse; Type: DATABASE; Schema: -; Owner: MoonlapseAdmin
--

CREATE DATABASE "Moonlapse" WITH TEMPLATE = template0 ENCODING = 'UTF8' LC_COLLATE = 'C.UTF-8' LC_CTYPE = 'C.UTF-8';


ALTER DATABASE "Moonlapse" OWNER TO "MoonlapseAdmin";

\connect "Moonlapse"

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: DATABASE "Moonlapse"; Type: COMMENT; Schema: -; Owner: MoonlapseAdmin
--

COMMENT ON DATABASE "Moonlapse" IS 'Database for the game MoonlapseMUD';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: entities; Type: TABLE; Schema: public; Owner: MoonlapseAdmin
--

CREATE TABLE public.entities (
    id integer NOT NULL,
    type character varying DEFAULT 'Entity'::character varying NOT NULL,
    lastupdated timestamp without time zone DEFAULT now() NOT NULL,
    "position" point,
    roomid integer
);


ALTER TABLE public.entities OWNER TO "MoonlapseAdmin";

--
-- Name: Entities_Id_seq; Type: SEQUENCE; Schema: public; Owner: MoonlapseAdmin
--

CREATE SEQUENCE public."Entities_Id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public."Entities_Id_seq" OWNER TO "MoonlapseAdmin";

--
-- Name: Entities_Id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: MoonlapseAdmin
--

ALTER SEQUENCE public."Entities_Id_seq" OWNED BY public.entities.id;


--
-- Name: rooms; Type: TABLE; Schema: public; Owner: MoonlapseAdmin
--

CREATE TABLE public.rooms (
    id integer NOT NULL,
    name character varying NOT NULL
);


ALTER TABLE public.rooms OWNER TO "MoonlapseAdmin";

--
-- Name: Maps_Id_seq; Type: SEQUENCE; Schema: public; Owner: MoonlapseAdmin
--

CREATE SEQUENCE public."Maps_Id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public."Maps_Id_seq" OWNER TO "MoonlapseAdmin";

--
-- Name: Maps_Id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: MoonlapseAdmin
--

ALTER SEQUENCE public."Maps_Id_seq" OWNED BY public.rooms.id;


--
-- Name: players; Type: TABLE; Schema: public; Owner: MoonlapseAdmin
--

CREATE TABLE public.players (
    entityid integer NOT NULL,
    userid integer NOT NULL,
    name character varying,
    "character" character(1)
);


ALTER TABLE public.players OWNER TO "MoonlapseAdmin";

--
-- Name: Players_EntityId_seq; Type: SEQUENCE; Schema: public; Owner: MoonlapseAdmin
--

CREATE SEQUENCE public."Players_EntityId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public."Players_EntityId_seq" OWNER TO "MoonlapseAdmin";

--
-- Name: Players_EntityId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: MoonlapseAdmin
--

ALTER SEQUENCE public."Players_EntityId_seq" OWNED BY public.players.entityid;


--
-- Name: Players_UserId_seq; Type: SEQUENCE; Schema: public; Owner: MoonlapseAdmin
--

CREATE SEQUENCE public."Players_UserId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public."Players_UserId_seq" OWNER TO "MoonlapseAdmin";

--
-- Name: Players_UserId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: MoonlapseAdmin
--

ALTER SEQUENCE public."Players_UserId_seq" OWNED BY public.players.userid;


--
-- Name: entities_roomid_seq; Type: SEQUENCE; Schema: public; Owner: MoonlapseAdmin
--

CREATE SEQUENCE public.entities_roomid_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.entities_roomid_seq OWNER TO "MoonlapseAdmin";

--
-- Name: entities_roomid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: MoonlapseAdmin
--

ALTER SEQUENCE public.entities_roomid_seq OWNED BY public.entities.roomid;


--
-- Name: portals; Type: TABLE; Schema: public; Owner: MoonlapseAdmin
--

CREATE TABLE public.portals (
    entityid integer NOT NULL,
    linkedposition point NOT NULL,
    linkedroomid integer NOT NULL
);


ALTER TABLE public.portals OWNER TO "MoonlapseAdmin";

--
-- Name: users; Type: TABLE; Schema: public; Owner: MoonlapseAdmin
--

CREATE TABLE public.users (
    id integer DEFAULT nextval('public."Entities_Id_seq"'::regclass) NOT NULL,
    username character varying NOT NULL,
    password character varying NOT NULL
);


ALTER TABLE public.users OWNER TO "MoonlapseAdmin";

--
-- Name: entities id; Type: DEFAULT; Schema: public; Owner: MoonlapseAdmin
--

ALTER TABLE ONLY public.entities ALTER COLUMN id SET DEFAULT nextval('public."Entities_Id_seq"'::regclass);


--
-- Name: players entityid; Type: DEFAULT; Schema: public; Owner: MoonlapseAdmin
--

ALTER TABLE ONLY public.players ALTER COLUMN entityid SET DEFAULT nextval('public."Players_EntityId_seq"'::regclass);


--
-- Name: players userid; Type: DEFAULT; Schema: public; Owner: MoonlapseAdmin
--

ALTER TABLE ONLY public.players ALTER COLUMN userid SET DEFAULT nextval('public."Players_UserId_seq"'::regclass);


--
-- Name: rooms id; Type: DEFAULT; Schema: public; Owner: MoonlapseAdmin
--

ALTER TABLE ONLY public.rooms ALTER COLUMN id SET DEFAULT nextval('public."Maps_Id_seq"'::regclass);


--
-- Name: entities entities_pkey; Type: CONSTRAINT; Schema: public; Owner: MoonlapseAdmin
--

ALTER TABLE ONLY public.entities
    ADD CONSTRAINT entities_pkey PRIMARY KEY (id);


--
-- Name: rooms maps_pkey; Type: CONSTRAINT; Schema: public; Owner: MoonlapseAdmin
--

ALTER TABLE ONLY public.rooms
    ADD CONSTRAINT maps_pkey PRIMARY KEY (id);


--
-- Name: players players_pkey; Type: CONSTRAINT; Schema: public; Owner: MoonlapseAdmin
--

ALTER TABLE ONLY public.players
    ADD CONSTRAINT players_pkey PRIMARY KEY (entityid, userid);


--
-- Name: portals portals_entityid_key; Type: CONSTRAINT; Schema: public; Owner: MoonlapseAdmin
--

ALTER TABLE ONLY public.portals
    ADD CONSTRAINT portals_entityid_key UNIQUE (entityid);


--
-- Name: portals portals_pkey; Type: CONSTRAINT; Schema: public; Owner: MoonlapseAdmin
--

ALTER TABLE ONLY public.portals
    ADD CONSTRAINT portals_pkey PRIMARY KEY (entityid);


--
-- Name: rooms rooms_name_key; Type: CONSTRAINT; Schema: public; Owner: MoonlapseAdmin
--

ALTER TABLE ONLY public.rooms
    ADD CONSTRAINT rooms_name_key UNIQUE (name);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: MoonlapseAdmin
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: MoonlapseAdmin
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: entities entities_roomid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: MoonlapseAdmin
--

ALTER TABLE ONLY public.entities
    ADD CONSTRAINT entities_roomid_fkey FOREIGN KEY (roomid) REFERENCES public.rooms(id);


--
-- Name: players players_entityid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: MoonlapseAdmin
--

ALTER TABLE ONLY public.players
    ADD CONSTRAINT players_entityid_fkey FOREIGN KEY (entityid) REFERENCES public.entities(id) ON UPDATE RESTRICT;


--
-- Name: players players_userid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: MoonlapseAdmin
--

ALTER TABLE ONLY public.players
    ADD CONSTRAINT players_userid_fkey FOREIGN KEY (userid) REFERENCES public.users(id) ON UPDATE RESTRICT;


--
-- Name: portals portals_entityid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: MoonlapseAdmin
--

ALTER TABLE ONLY public.portals
    ADD CONSTRAINT portals_entityid_fkey FOREIGN KEY (entityid) REFERENCES public.entities(id) ON DELETE CASCADE;


--
-- Name: portals portals_linkedroomid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: MoonlapseAdmin
--

ALTER TABLE ONLY public.portals
    ADD CONSTRAINT portals_linkedroomid_fkey FOREIGN KEY (linkedroomid) REFERENCES public.rooms(id);


--
-- PostgreSQL database dump complete
--

--
-- Database "postgres" dump
--

\connect postgres

--
-- PostgreSQL database dump
--

-- Dumped from database version 12.3 (Ubuntu 12.3-1.pgdg18.04+1)
-- Dumped by pg_dump version 12.3 (Ubuntu 12.3-1.pgdg18.04+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- PostgreSQL database dump complete
--

--
-- PostgreSQL database cluster dump complete
--
