# Data Sources

| Family | Source | Official Link | Local Path | Years | Purpose |
|---|---|---|---|---|---|
| SHSAT Admissions Outcomes | NYC DOE / InfoHub | [InfoHub](https://infohub.nyced.org/reports/admissions-and-enrollment/admissions-outcomes) | `data/raw/shsat/` | 2022–2026 | Feeder-school SHSAT testers and offer counts, used to construct participation (T1) and high-offer (T2) targets. |
| Demographic Snapshot | NYC DOE / InfoHub | [InfoHub](https://infohub.nyced.org/reports/students-and-schools/school-quality/information-and-data-overview) | `data/raw/demographics/` | 2021–22 to 2025–26 | School enrollment, demographic, and economic-need indicators, used as student-composition features. |
| ELA + Math Assessment Results | NYC DOE / InfoHub | [InfoHub](https://infohub.nyced.org/reports/academics/test-results) | `data/raw/assessments/` | 2022–2025 | School-level test scores by subject and grade, used as academic-performance features. |
| Middle School Directory | NYC DOE / InfoHub | [InfoHub](https://infohub.nyced.org/reports/admissions-and-enrollment/directory-data) | `data/raw/directory/` | 2022–2025 | School metadata (admissions method, size, programs, location), used as institutional features. |

All datasets are public. Download them and place the files under the corresponding local path to run the pipeline.
