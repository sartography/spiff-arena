## Updating from the Sartography upstream

1. In your checkout, set an `upstream` remote pointing to Sartography
1. Make a branch at our local main
1. Rebase your branch on top of upstream/main
1. Install dependencies (mysql-client, mariadb)
1. Ensure there's a sartography/sample-process-models clone next to spiff-arena
1. spiffworkflow-backend:

   1. In bin/recreate_db, uncomment the line `uv run flask db merge 1.
   1.

   ```bash
   rm uv.lock
   uv sync
   SPIFFWORKFLOW_BACKEND_DATABASE_TYPE=sqlite ./bin/recreate_db clean
   uv run pre-commit # run again to confirm it got everything; fix any problems
   ```

   1. recomment that line
1. commit changes
1. make a PR that _rebases_ this branch onto `origin/main`

