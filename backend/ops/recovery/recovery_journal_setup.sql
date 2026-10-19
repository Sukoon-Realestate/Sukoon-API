-- Execute on the independently provisioned journal cluster as its schema owner.
-- psql variables: journal_environment, journal_role. Create its LOGIN credential
-- out of band; this script does not print or store passwords.
BEGIN;
CREATE SCHEMA sokoun_recovery;
REVOKE ALL ON SCHEMA sokoun_recovery FROM PUBLIC;
CREATE TABLE sokoun_recovery.identity (
 singleton boolean PRIMARY KEY DEFAULT true CHECK (singleton),
 cluster_id text NOT NULL,
 environment text NOT NULL
);
INSERT INTO sokoun_recovery.identity(cluster_id, environment)
 SELECT system_identifier::text, :'journal_environment' FROM pg_control_system();
CREATE TABLE sokoun_recovery.entries (
 sequence bigint PRIMARY KEY CHECK (sequence > 0),
 payload jsonb NOT NULL,
 checksum text UNIQUE NOT NULL CHECK (length(checksum)=64),
 previous text UNIQUE NOT NULL,
 CHECK (jsonb_typeof(payload)='object')
);
REVOKE ALL ON ALL TABLES IN SCHEMA sokoun_recovery FROM PUBLIC;
GRANT USAGE ON SCHEMA sokoun_recovery TO :"journal_role";
GRANT SELECT ON sokoun_recovery.identity TO :"journal_role";
GRANT SELECT, INSERT ON sokoun_recovery.entries TO :"journal_role";
GRANT EXECUTE ON FUNCTION pg_control_system() TO :"journal_role";
COMMIT;
