# Islamic Educational Complex (edu_islamic_complex)

End-to-end Odoo 19 module suite for managing an Islamic Educational Complex: students, guardians, levels, groups,
enrollments, assignments, scheduling, attendance, evaluations, and fees with invoicing.

## Key Features

- Student intake with placement wizard and teacher suggestions
- Level + class group management with capacity enforcement
- Teacher assignments (1:1 or group) with automated session generation
- Session scheduling with auto attendance sheets
- Evaluation rubric and progress analytics (pivot/graph)
- Fees plans and invoice integration with overdue tracking
- Multi-company compatible and Arabic/English UI

## Roles

- **Islamic School Admin**: Full access to all education models
- **Academic Coordinator**: Manage academic entities, schedules, assignments, evaluations
- **Teacher**: View assigned students/groups, mark attendance, create evaluations
- **Finance Officer**: Fees plans and invoices only
- **Guardian Portal**: Read-only access to student attendance/evaluations (optional)

## Installation (Ubuntu 24.04)

1. Copy/add this module to your custom addons path:
    - `/mnt/d/00Github/OdooProjects/ti_addons/edu_islamic_complex`
2. Update your Odoo config to include the addons path, e.g.:
    - `addons_path = /path/to/odoo/addons,/mnt/d/00Github/OdooProjects/ti_addons`
3. Restart Odoo and update the apps list.
4. Install **Islamic Educational Complex** from Apps.

## Update / Upgrade

```bash
./odoo-bin -c /etc/odoo/odoo.conf -u edu_islamic_complex
```

## Common Commands

```bash
# Start Odoo in dev mode
./odoo-bin -c /etc/odoo/odoo.conf --dev=all

# Update just this module
./odoo-bin -c /etc/odoo/odoo.conf -u edu_islamic_complex
```

## Configuration

- Settings → Education:
    - Enable gender constraints
    - Default session duration and recurrence weeks
    - Fee overdue blocking and thresholds
    - Default invoice product and journal

## Main Workflows

1. **Student Intake & Placement**
    - Create student + guardian
    - Use the Placement wizard to set level and optional teacher assignment
2. **Assignments & Scheduling**
    - Assign teacher to student or class group
    - Generate sessions (weekly recurrence)
3. **Attendance**
    - Open sessions and mark attendance
    - Review attendance KPIs
4. **Evaluations**
    - Create evaluations from rubric fields
    - Review in pivot/graph views
5. **Fees & Invoices**
    - Create fees plans per level
    - Create invoices from enrollment and track overdue

## Notes

- Teachers are `hr.employee` records with **Is Teacher** enabled or job title matching “Teacher/معلم”.
- Students are stored in `edu_student` (not `res.partner` by default). A billing partner is created if needed.
- For Guardian Portal access, link a guardian to a user record in `edu_guardian`.
