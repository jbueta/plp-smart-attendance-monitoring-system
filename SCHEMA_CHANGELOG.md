# Schema Changelog

This file tracks schema decisions, repo-to-database alignment, and proposed DB changes for team discussion.

## 2026-04-23

### Repo Realigned To Current Local MariaDB Schema

The codebase was updated to match the actual running local database instead of the previously assumed schema extension.

Current aligned structure:
- `employees.seq` exists and is `AUTO_INCREMENT UNIQUE`
- `employees.employee_id` is currently `VARCHAR(8)`
- checked-in employee trigger format is aligned to `EMP-0001`
- `employees` does **not** have `is_active`
- `visitors.seq` exists and is `AUTO_INCREMENT UNIQUE`
- `visitors.visitor_id` is currently `VARCHAR(8)`
- checked-in visitor trigger format is aligned to `VT-00001`
- `visitors` does **not** have `details`
- `visitors` does **not** have `is_active`
- soft-active behavior is handled through `users.active`

Code impact:
- removed queries that referenced `visitors.details`
- removed queries that referenced `employees.is_active`
- removed queries that referenced `visitors.is_active`
- visitor check-in/edit flows now store only fields that actually exist in the live DB
- visitor UI was simplified to show `visitor_id` instead of the removed `details` field

Schema impact in `schema.sql`:
- `employees.employee_id` aligned back to `VARCHAR(8)`
- `visitors.visitor_id` aligned back to `VARCHAR(8)`
- removed repo-only `employees.is_active`
- removed repo-only `visitors.details`
- removed repo-only `visitors.is_active`

### Pending Proposal For Group Discussion

These are still reasonable future changes, but they are **not** part of the currently aligned live schema:
- increase `employees.employee_id` to `VARCHAR(12)`
- increase `visitors.visitor_id` to `VARCHAR(12)`
- optionally add a real `visitors.details` column if the team wants to store person/office to visit
- optionally add table-level active flags if the team wants status separated from `users.active`

Suggested discussion points:
- Should `users.active` remain the single source of truth for soft-deactivated accounts?
- Should `visitor_id` and `employee_id` stay as business/display IDs while `user_id` or `seq` is treated as the real internal key?
- Do you want to formalize future DB changes as migration scripts instead of only editing `schema.sql`?

### If The Team Approves Larger IDs Later

Example future migration:

```sql
ALTER TABLE visitors MODIFY visitor_id VARCHAR(12) NOT NULL;
ALTER TABLE employees MODIFY employee_id VARCHAR(12) NOT NULL;
```
