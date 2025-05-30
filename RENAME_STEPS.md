# SiteSentinel Rebranding Guide

The project has been renamed from "Website Monitoring System" to "SiteSentinel". The following changes have been made:

1. Updated README.md title and references
2. Updated main.py banner text and log messages
3. Changed database name from "website_monitor" to "sitesentinel"
4. Updated setup_postgres.sh script references
5. Renamed the main log file

## Complete the GitHub Changes

To complete the rebranding and push these changes to GitHub:

1. The local changes have been committed to the `rename-to-sitesentinel` branch.

2. Push the branch to GitHub:
```bash
git push -u origin rename-to-sitesentinel
```

3. Create a pull request on GitHub:
   - Go to: https://github.com/ncandio/Health_Check_PostgreSQL
   - Click on "Compare & pull request" for the rename-to-sitesentinel branch
   - Title: "Rename project to SiteSentinel"
   - Description: Use the commit message as a starting point

4. After the PR is merged, consider:
   - Updating the GitHub repository name from "Health_Check_PostgreSQL" to "SiteSentinel"
   - Creating a new logo for SiteSentinel
   - Updating any external documentation or references

## Local Repository Rename

After completing the GitHub renaming:

1. Clone the repository with the new name:
```bash
git clone https://github.com/ncandio/SiteSentinel.git
```

2. Copy any uncommitted files from the old directory to the new one.

3. Update your local development environment to work with the new repository.

4. Delete the old repository directory if no longer needed.

## Database Migration

If you have an existing database:

1. Create a backup of your current "website_monitor" database:
```bash
pg_dump -U postgres -d website_monitor > website_monitor_backup.sql
```

2. Create the new "sitesentinel" database:
```bash
createdb -U postgres sitesentinel
```

3. Restore the backup to the new database:
```bash
psql -U postgres -d sitesentinel < website_monitor_backup.sql
```

4. Verify the migration:
```bash
psql -U postgres -d sitesentinel -c "SELECT COUNT(*) FROM website_configs;"
```