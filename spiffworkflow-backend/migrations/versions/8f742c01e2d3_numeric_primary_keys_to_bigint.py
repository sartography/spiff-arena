"""numeric primary keys to bigint

Revision ID: 8f742c01e2d3
Revises: d9d54e36c69f
Create Date: 2026-06-30 00:00:00.000000

"""
# ruff: noqa: S608
from alembic import op

# revision identifiers, used by Alembic.
revision = "8f742c01e2d3"
down_revision = "d9d54e36c69f"
branch_labels = None
depends_on = None


def _alter_integer_key_type_sql(from_type: str, to_type: str) -> str:
    return f"""
DO $$
DECLARE
  statement text;
  statements text[];
BEGIN
  WITH selected_pk AS (
      SELECT c.oid, c.conrelid, c.conname, c.conkey
      FROM pg_constraint c
      JOIN pg_class r ON r.oid = c.conrelid
      JOIN pg_namespace n ON n.oid = r.relnamespace
      WHERE c.contype = 'p'
        AND n.nspname NOT IN ('pg_catalog', 'information_schema')
        AND n.nspname !~ '^pg_toast'
        AND NOT EXISTS (
          SELECT 1
          FROM unnest(c.conkey) AS k(attnum)
          JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = k.attnum
          WHERE a.atttypid <> 'pg_catalog.{from_type}'::regtype
        )
    ),
    selected_fk AS (
      SELECT DISTINCT c.oid, c.conrelid, c.conname, c.conkey, c.confrelid
      FROM pg_constraint c
      JOIN selected_pk pk ON pk.conrelid = c.confrelid AND pk.conkey = c.confkey
      WHERE c.contype = 'f'
    ),
    target_columns AS (
      SELECT DISTINCT pk.conrelid AS relid, k.attnum
      FROM selected_pk pk
      CROSS JOIN LATERAL unnest(pk.conkey) AS k(attnum)
      UNION
      SELECT DISTINCT fk.conrelid AS relid, k.attnum
      FROM selected_fk fk
      CROSS JOIN LATERAL unnest(fk.conkey) AS k(attnum)
    ),
    typed_target_columns AS (
      SELECT c.relid, c.attnum, n.nspname, r.relname, a.attname
      FROM target_columns c
      JOIN pg_class r ON r.oid = c.relid
      JOIN pg_namespace n ON n.oid = r.relnamespace
      JOIN pg_attribute a ON a.attrelid = c.relid AND a.attnum = c.attnum
      WHERE a.atttypid = 'pg_catalog.{from_type}'::regtype
    ),
    statements AS (
      SELECT
        10 AS phase,
        format('%s.%s.%s', n.nspname, r.relname, fk.conname) AS sort_key,
        format('ALTER TABLE %I.%I DROP CONSTRAINT %I', n.nspname, r.relname, fk.conname) AS sql
      FROM selected_fk fk
      JOIN pg_class r ON r.oid = fk.conrelid
      JOIN pg_namespace n ON n.oid = r.relnamespace

      UNION ALL

      SELECT
        20 AS phase,
        format('%s.%s.%s', n.nspname, r.relname, pk.conname) AS sort_key,
        format('ALTER TABLE %I.%I DROP CONSTRAINT %I', n.nspname, r.relname, pk.conname) AS sql
      FROM selected_pk pk
      JOIN pg_class r ON r.oid = pk.conrelid
      JOIN pg_namespace n ON n.oid = r.relnamespace

      UNION ALL

      SELECT
        30 AS phase,
        format('%s.%s.%s', nspname, relname, attname) AS sort_key,
        format('ALTER TABLE %I.%I ALTER COLUMN %I TYPE {to_type}', nspname, relname, attname) AS sql
      FROM typed_target_columns

      UNION ALL

      SELECT
        40 AS phase,
        format('%s.%s.%s', n.nspname, r.relname, pk.conname) AS sort_key,
        format('ALTER TABLE %I.%I ADD CONSTRAINT %I %s', n.nspname, r.relname, pk.conname, pg_get_constraintdef(pk.oid)) AS sql
      FROM selected_pk pk
      JOIN pg_class r ON r.oid = pk.conrelid
      JOIN pg_namespace n ON n.oid = r.relnamespace

      UNION ALL

      SELECT
        50 AS phase,
        format('%s.%s.%s', n.nspname, r.relname, fk.conname) AS sort_key,
        format(
          'ALTER TABLE %I.%I ADD CONSTRAINT %I %s NOT VALID',
          n.nspname,
          r.relname,
          fk.conname,
          regexp_replace(pg_get_constraintdef(fk.oid), '[[:space:]]+NOT VALID$', '', 'i')
        ) AS sql
      FROM selected_fk fk
      JOIN pg_class r ON r.oid = fk.conrelid
      JOIN pg_namespace n ON n.oid = r.relnamespace

      UNION ALL

      SELECT
        60 AS phase,
        format('%s.%s.%s', n.nspname, r.relname, fk.conname) AS sort_key,
        format('ALTER TABLE %I.%I VALIDATE CONSTRAINT %I', n.nspname, r.relname, fk.conname) AS sql
      FROM selected_fk fk
      JOIN pg_class r ON r.oid = fk.conrelid
      JOIN pg_namespace n ON n.oid = r.relnamespace
    )
  SELECT array_agg(sql ORDER BY phase, sort_key)
  INTO statements
  FROM statements;

  IF statements IS NULL THEN
    RAISE NOTICE 'No matching integer key columns found.';
    RETURN;
  END IF;

  FOREACH statement IN ARRAY statements
  LOOP
    EXECUTE statement;
  END LOOP;
END $$;
"""


def upgrade():
    if op.get_bind().dialect.name == "postgresql":
        op.execute(_alter_integer_key_type_sql("int4", "bigint"))


def downgrade():
    if op.get_bind().dialect.name == "postgresql":
        op.execute(_alter_integer_key_type_sql("int8", "integer"))
