# Employee Management Database

## Overview

This relational design tracks departments, employees, projects, and employee assignments to projects. An employee belongs to one department. Employees and projects have a many-to-many relationship, represented by `EMPLOYEE_PROJECTS`.

The scripts use standard SQL data types and explicit IDs in the sample data. Run `01_create_tables.sql` first, followed by `02_insert_sample_data.sql`.

## ER diagram

```mermaid
erDiagram
    DEPARTMENTS ||--o{ EMPLOYEES : contains
    EMPLOYEES ||--o{ EMPLOYEE_PROJECTS : assigned_to
    PROJECTS ||--o{ EMPLOYEE_PROJECTS : includes

    DEPARTMENTS {
        INTEGER department_id PK
        VARCHAR department_name UK
        VARCHAR location
        DECIMAL annual_budget
    }
    EMPLOYEES {
        INTEGER employee_id PK
        VARCHAR first_name
        VARCHAR last_name
        VARCHAR email UK
        VARCHAR job_title
        DATE hire_date
        DECIMAL salary
        INTEGER department_id FK
    }
    PROJECTS {
        INTEGER project_id PK
        VARCHAR project_name UK
        DATE start_date
        DATE end_date
        VARCHAR status
        DECIMAL budget
    }
    EMPLOYEE_PROJECTS {
        INTEGER employee_id PK, FK
        INTEGER project_id PK, FK
        DATE assigned_date
        VARCHAR project_role
        DECIMAL allocation_percent
    }
```

## Table definitions and keys

| Table | Purpose | Primary key | Foreign keys and constraints |
|---|---|---|---|
| `DEPARTMENTS` | Department name, location, and annual budget | `department_id` | `department_name` is unique; `annual_budget` must be non-negative |
| `EMPLOYEES` | Employee identity, work details, salary, and department | `employee_id` | `department_id` references `DEPARTMENTS.department_id`; `email` is unique; `salary` must be non-negative |
| `PROJECTS` | Project schedule, status, and budget | `project_id` | `project_name` is unique; `end_date` cannot precede `start_date`; `status` is limited to Planned, Active, or Completed; `budget` must be non-negative |
| `EMPLOYEE_PROJECTS` | Assignment of employees to projects, including their role and allocation | (`employee_id`, `project_id`) | `employee_id` references `EMPLOYEES.employee_id`; `project_id` references `PROJECTS.project_id`; allocation must be between 0 and 100 percent |

## Sample data

The insert script contains 5 departments, 20 employees, 10 projects, and 30 employee-to-project assignments.

## Scripts

- [01_create_tables.sql](./01_create_tables.sql) — creates all four tables and their primary key, foreign key, unique, and check constraints.
- [02_insert_sample_data.sql](./02_insert_sample_data.sql) — inserts the sample records in foreign-key-safe order.
