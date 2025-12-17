# Athletics Performance Analytics

## Project Overview
This project analyzes a collegiate athletics performance database that integrates data from three monitoring systems: **Hawkins force plates, Kinexon GPS/accelerometry, and Vald strength testing**. **Python and SQL** were used to clean, transform, and analyze longitudinal althlete performance data to generate insights on performance monitoring. These findings can help coaches and practitioners support athlete readiness and training decisions.

## Team Members & Roles
- **Aima Chaudhry**:
  - 1.4 Brief Review Of Literature & Metric Selection
  - 2.1 Missing Data Analysis
  - 4.2 Research Synthesis & Recommendations (Methods),
  - 4.3 Final Presentation (Methods/Tableau Dashboard)
- **Nabiha Chaudhry**:
  - 1.2 Data Quality Assessment
  - 3.2 Team Comparison Analysis
  - 4.2 Research Synthesis & Recommendations (Results)
  - 4.3 Final Presentation (Key Findings)
- **Nawal Choudhry**:
  - 2.3 Create a Derived Metric
  - 3.3 Dashboard Metric
  - 4.2 Research Synthesis & Recommendations (Limitations & Future Directions)
  - 4.3 Final Presentation (Limitations & Future Work)
- **Breanna Hardy**:
  - 1.4 Brief Review Of Literature & Metric Selection
  - 4.1 Performance Monitoring Flag System
  - 4.2 Research Synthesis & Recommendations (Discussion)
  - 4.3 Final Presentation (Practical Applications)
- **Jenny Lin**:
  - 2.2 Data Transformation Challenge
  - 4.1 Performance Monitoring Flag System
  - 4.2 Research Synthesis & Recommendations (Introduction)
  - 4.3 Final Presentation (Introduction)
- **Rujula Patole**:
  - 1.3 Metric Discovery & Selection
  - 3.1 Individual Athlete Timeline
  - 4.3 Final Presentation (Key Findings)
 
## Project Structure
```
507_groupproject_2025/
├── README.md 
├── references.md
├── .env.example
├── .gitignore
├── part1_exploration.py
├── part1_summary.pdf
├── part1_literature_review.pdf
├── part2_cleaning.py
├── part3_viz_individual.ipynb
├── part3_viz_comparison.ipynb
├── part4_flags.py
├── part4_flagged_athletes.csv
├── part4_flag_justification.pdf
├── part4_research_synthesis.pdf
└── final_presentation.pdf
```
## Setup Instructions
1. Clone Repository
```
git clone https://github.com/aimachaudhry/507_groupproject_2025.git
cd 507_groupproject_2025
```
2. Create Virtual Environment
```
python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```
3. Install Dependencies
```
pip install -r requirements.txt
```
Required Libraries:
```
pandas
SQLAlchemy
pymysql
matplotlib
seaborn
numpy
scipy
python-dotenv
```

## Database Connection
Create .env file and fill in actual credentials:
```python
DB_HOST=your_database_host
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=database_name
DB_TABLE=research_experiment_refactor_test
```
Connection Template:
```python
from sqlalchemy import create_engine
import pandas as pd
# Connection string 
engine = create_engine(
    "mysql+pymysql://username:password@host:port/database_name"
)

# Example query
query = "SELECT * FROM research_experiment_refactor_test LIMIT 10"
df = pd.read_sql(query, engine)

# Close connection when done
engine.dispose()
```

Successful Connection:
- **Aima**:

<img width="600" height="300" alt="Screenshot 2025-12-16 at 2 46 58 PM" src="https://github.com/user-attachments/assets/866098be-6eb0-4370-93a1-84676a2d5c10" />

- **Nabiha**:
  
<img width="600" height="300" alt="Screenshot 2025-12-17 at 12 25 44 AM" src="https://github.com/user-attachments/assets/61ab23a4-b9fb-444c-a1a6-f0e068a586f0" />

- **Nawal**:
- **Breanna**:
<img width="600" height="300" alt="Screenshot 2025-12-17 at 12 28 13 AM" src="https://github.com/user-attachments/assets/dff80ee8-0984-4437-96f6-72019738a300" />


- **Jenny**:
- **Rujula**:
<img width="600" height="300" alt="Screenshot 2025-12-17 at 4 28 24 PM" src="https://github.com/user-attachments/assets/443ea5df-1870-4342-8eea-b40d3df7694a" />


## Running Each Script:

### Part 1: Database Connection & Data Exploration
- ```part1_exploration.py```: Outputs summary statistics and metric counts by data source
- ```part1_summary.pdf```: Summary report on data quality assessment of database
-  ```part1_literature_review.pdf```: Literature review on selected metrics

### Part 2: Data Cleaning & Transformation
```
part2_cleaning.py
```
- Analyzes Missing Data
- Transforms data from long to wide format
- Calculates team-based derived metrics

### Part 3: Longitudinal Analysis & Visualization

1. Open notebook in Colab
2. Create .env file and connect to the database by filling in actual credentials
3. Run all cells

```part3_viz_individual.ipynb```: Analyzes the performance trends of two athletes from men's basketball

```part3_viz_comparison.ipynb```: Compares men's and women's basketball using t-tests and visualizations such as box plots

### Part 4: Research Synthesis & Application
```
part4_flags.py
```
- Creates a **Performance Monitoring Flag System**
- Generates ```part4_flagged_athletes.csv```
- ```part4_flag_justification.pdf```: literature-based thresholds

### Tableau Dashboard
- [Link to Tableau Dashboard](https://public.tableau.com/app/profile/aima.chaudhry/viz/AthleticsPerformance/Dashboard2)
- Creates visualizations of Data Quality, Team-Relative Performance, and Two-Athlete Performance Trends 




