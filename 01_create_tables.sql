CREATE TABLE DEPARTMENTS (
    department_id INTEGER NOT NULL,
    department_name VARCHAR(100) NOT NULL,
    location VARCHAR(100) NOT NULL,
    annual_budget DECIMAL(14, 2) NOT NULL,
    CONSTRAINT pk_departments PRIMARY KEY (department_id),
    CONSTRAINT uq_departments_name UNIQUE (department_name),
    CONSTRAINT ck_departments_budget CHECK (annual_budget >= 0)
);

CREATE TABLE EMPLOYEES (
    employee_id INTEGER NOT NULL,
    first_name VARCHAR(60) NOT NULL,
    last_name VARCHAR(60) NOT NULL,
    email VARCHAR(254) NOT NULL,
    job_title VARCHAR(100) NOT NULL,
    hire_date DATE NOT NULL,
    salary DECIMAL(12, 2) NOT NULL,
    department_id INTEGER NOT NULL,
    CONSTRAINT pk_employees PRIMARY KEY (employee_id),
    CONSTRAINT uq_employees_email UNIQUE (email),
    CONSTRAINT ck_employees_salary CHECK (salary >= 0),
    CONSTRAINT fk_employees_department
        FOREIGN KEY (department_id) REFERENCES DEPARTMENTS (department_id)
);

CREATE TABLE PROJECTS (
    project_id INTEGER NOT NULL,
    project_name VARCHAR(150) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    status VARCHAR(20) NOT NULL,
    budget DECIMAL(14, 2) NOT NULL,
    CONSTRAINT pk_projects PRIMARY KEY (project_id),
    CONSTRAINT uq_projects_name UNIQUE (project_name),
    CONSTRAINT ck_projects_dates CHECK (end_date IS NULL OR end_date >= start_date),
    CONSTRAINT ck_projects_status CHECK (status IN ('Planned', 'Active', 'Completed')),
    CONSTRAINT ck_projects_budget CHECK (budget >= 0)
);

CREATE TABLE EMPLOYEE_PROJECTS (
    employee_id INTEGER NOT NULL,
    project_id INTEGER NOT NULL,
    assigned_date DATE NOT NULL,
    project_role VARCHAR(100) NOT NULL,
    allocation_percent DECIMAL(5, 2) NOT NULL,
    CONSTRAINT pk_employee_projects PRIMARY KEY (employee_id, project_id),
    CONSTRAINT ck_employee_projects_allocation
        CHECK (allocation_percent >= 0 AND allocation_percent <= 100),
    CONSTRAINT fk_employee_projects_employee
        FOREIGN KEY (employee_id) REFERENCES EMPLOYEES (employee_id),
    CONSTRAINT fk_employee_projects_project
        FOREIGN KEY (project_id) REFERENCES PROJECTS (project_id)
);
