INSERT INTO DEPARTMENTS (department_id, department_name, location, annual_budget) VALUES
    (1, 'Engineering', 'Bengaluru', 2500000.00),
    (2, 'Human Resources', 'Bengaluru', 800000.00),
    (3, 'Finance', 'Chennai', 1000000.00),
    (4, 'Sales', 'Mumbai', 1400000.00),
    (5, 'Marketing', 'Hyderabad', 900000.00);

INSERT INTO EMPLOYEES
    (employee_id, first_name, last_name, email, job_title, hire_date, salary, department_id)
VALUES
    (1, 'Aarav', 'Sharma', 'aarav.sharma@example.com', 'Engineering Manager', '2020-03-16', 1450000.00, 1),
    (2, 'Diya', 'Patel', 'diya.patel@example.com', 'Software Engineer', '2021-06-07', 950000.00, 1),
    (3, 'Ishaan', 'Rao', 'ishaan.rao@example.com', 'Software Engineer', '2022-01-10', 880000.00, 1),
    (4, 'Ananya', 'Nair', 'ananya.nair@example.com', 'Database Engineer', '2019-11-18', 1200000.00, 1),
    (5, 'Vihaan', 'Iyer', 'vihaan.iyer@example.com', 'QA Engineer', '2023-02-13', 720000.00, 1),
    (6, 'Meera', 'Joshi', 'meera.joshi@example.com', 'HR Manager', '2018-08-20', 1100000.00, 2),
    (7, 'Arjun', 'Menon', 'arjun.menon@example.com', 'Recruiter', '2020-05-04', 680000.00, 2),
    (8, 'Saanvi', 'Reddy', 'saanvi.reddy@example.com', 'HR Specialist', '2022-09-12', 640000.00, 2),
    (9, 'Kabir', 'Gupta', 'kabir.gupta@example.com', 'Finance Manager', '2017-04-03', 1350000.00, 3),
    (10, 'Aditi', 'Kulkarni', 'aditi.kulkarni@example.com', 'Accountant', '2020-10-19', 760000.00, 3),
    (11, 'Reyansh', 'Desai', 'reyansh.desai@example.com', 'Financial Analyst', '2021-12-06', 820000.00, 3),
    (12, 'Ira', 'Pillai', 'ira.pillai@example.com', 'Accountant', '2023-04-17', 610000.00, 3),
    (13, 'Advik', 'Verma', 'advik.verma@example.com', 'Sales Manager', '2019-01-14', 1280000.00, 4),
    (14, 'Myra', 'Chopra', 'myra.chopra@example.com', 'Account Executive', '2020-07-27', 780000.00, 4),
    (15, 'Krish', 'Bose', 'krish.bose@example.com', 'Account Executive', '2022-03-21', 740000.00, 4),
    (16, 'Tara', 'Saxena', 'tara.saxena@example.com', 'Sales Analyst', '2023-08-01', 650000.00, 4),
    (17, 'Rohan', 'Khan', 'rohan.khan@example.com', 'Marketing Manager', '2018-06-11', 1220000.00, 5),
    (18, 'Kiara', 'Mishra', 'kiara.mishra@example.com', 'Content Strategist', '2020-02-24', 770000.00, 5),
    (19, 'Atharv', 'Singh', 'atharv.singh@example.com', 'Marketing Analyst', '2021-09-06', 810000.00, 5),
    (20, 'Pari', 'Das', 'pari.das@example.com', 'Graphic Designer', '2023-05-15', 620000.00, 5);

INSERT INTO PROJECTS (project_id, project_name, start_date, end_date, status, budget) VALUES
    (1, 'Customer Portal', '2024-01-15', NULL, 'Active', 850000.00),
    (2, 'Data Warehouse Modernization', '2023-09-01', NULL, 'Active', 1250000.00),
    (3, 'Employee Self-Service Platform', '2023-03-01', '2024-02-28', 'Completed', 620000.00),
    (4, 'Financial Reporting Automation', '2024-04-01', NULL, 'Active', 430000.00),
    (5, 'Sales CRM Upgrade', '2024-02-01', NULL, 'Active', 710000.00),
    (6, 'Brand Refresh', '2023-10-01', '2024-06-30', 'Completed', 360000.00),
    (7, 'Recruitment Analytics', '2024-05-01', NULL, 'Active', 280000.00),
    (8, 'Mobile Application', '2025-01-15', NULL, 'Planned', 980000.00),
    (9, 'Marketing Campaign Insights', '2024-07-01', NULL, 'Active', 390000.00),
    (10, 'Quality Engineering Initiative', '2025-02-01', NULL, 'Planned', 320000.00);

INSERT INTO EMPLOYEE_PROJECTS
    (employee_id, project_id, assigned_date, project_role, allocation_percent)
VALUES
    (1, 1, '2024-01-15', 'Project Sponsor', 10.00),
    (2, 1, '2024-01-15', 'Frontend Engineer', 60.00),
    (3, 1, '2024-01-22', 'Backend Engineer', 70.00),
    (4, 2, '2023-09-01', 'Data Architect', 60.00),
    (2, 2, '2023-10-02', 'Application Engineer', 20.00),
    (5, 10, '2025-02-01', 'QA Lead', 50.00),
    (6, 3, '2023-03-01', 'Project Sponsor', 10.00),
    (7, 7, '2024-05-01', 'HR Data Analyst', 60.00),
    (8, 3, '2023-03-06', 'Requirements Analyst', 40.00),
    (9, 4, '2024-04-01', 'Project Sponsor', 10.00),
    (10, 4, '2024-04-01', 'Finance Subject Matter Expert', 50.00),
    (11, 2, '2023-09-11', 'Financial Analyst', 25.00),
    (12, 4, '2024-04-08', 'Reporting Analyst', 40.00),
    (13, 5, '2024-02-01', 'Project Sponsor', 10.00),
    (14, 5, '2024-02-01', 'Business Lead', 50.00),
    (15, 5, '2024-02-05', 'Sales Representative', 40.00),
    (16, 5, '2024-02-12', 'Data Analyst', 30.00),
    (17, 6, '2023-10-01', 'Project Sponsor', 10.00),
    (18, 6, '2023-10-02', 'Content Lead', 50.00),
    (20, 6, '2023-10-02', 'Visual Designer', 40.00),
    (19, 9, '2024-07-01', 'Marketing Analyst', 60.00),
    (18, 9, '2024-07-01', 'Content Strategist', 20.00),
    (1, 8, '2025-01-15', 'Technical Sponsor', 10.00),
    (2, 8, '2025-01-15', 'Mobile Engineer', 50.00),
    (3, 8, '2025-01-15', 'API Engineer', 50.00),
    (4, 8, '2025-01-20', 'Data Engineer', 25.00),
    (6, 7, '2024-05-01', 'Project Sponsor', 10.00),
    (9, 2, '2023-09-01', 'Project Sponsor', 10.00),
    (13, 9, '2024-07-01', 'Business Sponsor', 10.00),
    (17, 9, '2024-07-01', 'Campaign Sponsor', 10.00);
