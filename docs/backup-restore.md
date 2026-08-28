# Morning backup and restore

Morning launches with a fresh production database; these procedures protect Morning data created after cutover. There is no legacy Atlas/SQLite data migration requirement.

## Backup

With PostgreSQL client tools installed:

```sh
export MORNING_DATABASE_URL='postgresql://...'
scripts/backup.sh
```

The script creates a timestamped custom-format `pg_dump` under `./backups` unless `MORNING_BACKUP_DIR` is set.

## Restore drill

Restore into an empty disposable PostgreSQL database first:

```sh
export MORNING_DATABASE_URL='postgresql://.../morning_restore_test'
scripts/restore.sh ./backups/morning-YYYYMMDDTHHMMSSZ.dump
```

Then verify:

- configured machines, crews and personnel are present;
- at least one submitted shift report can be opened;
- the same 24-hour report renders before and after restore;
- machine-state declarations retain their provenance.

A controlled rollout is not considered ready until this restore drill has been performed against a production-shaped dataset.
