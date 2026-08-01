-- Drop Neon Auth foreign keys so user_id can store Cognito subs.
-- Safe to re-run: missing constraints are ignored.

DO $$
DECLARE
  r record;
BEGIN
  FOR r IN
    SELECT c.conname, n.nspname AS schema_name, rel.relname AS table_name
    FROM pg_constraint c
    JOIN pg_class rel ON rel.oid = c.conrelid
    JOIN pg_namespace n ON n.oid = rel.relnamespace
    JOIN pg_class ref ON ref.oid = c.confrelid
    JOIN pg_namespace rn ON rn.oid = ref.relnamespace
    WHERE c.contype = 'f'
      AND n.nspname = 'consulting_tracker'
      AND rn.nspname = 'neon_auth'
      AND ref.relname = 'user'
  LOOP
    EXECUTE format(
      'ALTER TABLE %I.%I DROP CONSTRAINT IF EXISTS %I',
      r.schema_name,
      r.table_name,
      r.conname
    );
  END LOOP;
END $$;
