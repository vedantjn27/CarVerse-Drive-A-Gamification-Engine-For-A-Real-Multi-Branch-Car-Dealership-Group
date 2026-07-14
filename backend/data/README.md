# CarVerse source data

This directory contains byte-for-byte copies of all three organizer-provided CSV
files. The originals under the workspace's `carverse files/` folder remain
untouched and authoritative.

Verified Phase 1 data rows:

- `z_locations.csv`: 41
- `z_employees.csv`: 6,037
- `z_event_log_may_june_2026.csv`: 170,162

The startup lifecycle validates the filenames and exact headers before resetting
the disposable schema, then ingests every row. Raw categorical/action values are
stored beside normalized values to keep cleanup decisions auditable.

SQLite files created at runtime are intentionally ignored.
