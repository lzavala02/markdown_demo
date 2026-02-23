# Poetry and Streamlit Setup Guide

## Poetry Setup

Poetry is a modern Python dependency manager that provides better version control and reproducibility than pip.

### Install Poetry

#### Windows:
```bash
# Using pip
pip install poetry

# Or using winget
winget install python-poetry.python-poetry

# Or download from https://github.com/python-poetry/poetry/releases
```

#### macOS/Linux:
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

### Verify Installation

```bash
poetry --version
```

### Using Poetry with This Project

#### 1. Install Dependencies

```bash
poetry install
```

This command:
- Creates a virtual environment automatically
- Installs all dependencies from `pyproject.toml`
- Creates a `poetry.lock` file (locks exact versions)
- Sets up the project in development mode

#### 2. Run Commands in Poetry Environment

```bash
# Run the main CLI application
poetry run python main.py

# Run tests with coverage
poetry run pytest test_suite.py -v --cov=.

# Run Streamlit dashboard
poetry run streamlit run streamlit_app.py
```

#### 3. Activate the Virtual Environment

```bash
# On Windows
poetry shell

# Then run commands directly
python main.py
pytest test_suite.py -v
streamlit run streamlit_app.py

# Exit the environment
exit
```

#### 4. Add New Dependencies

```bash
poetry add package_name

# Or add as dev dependency
poetry add --group dev package_name
```

#### 5. Update Dependencies

```bash
poetry update
```

#### 6. Export to requirements.txt (if needed)

```bash
poetry export -f requirements.txt --output requirements.txt
```

---

## Streamlit Dashboard

Streamlit provides an interactive web interface for the data consolidation system.

### Running Streamlit

```bash
poetry run streamlit run streamlit_app.py

# Or if you're in the poetry shell
streamlit run streamlit_app.py
```

The application will open at: `http://localhost:8501`

### Streamlit Features

The dashboard provides 9 interactive pages:

#### 1. **🏠 Dashboard** - Overview
- Summary of all 10 Acceptance Criteria
- Quick start guide
- Feature overview

#### 2. **📥 Import Data** - File Upload
- Select data source type (production, quality, shipping)
- Upload CSV or Excel file
- View import results and error messages

#### 3. **🔍 Lot Lookup** - Consolidated View
- Search by Lot ID or Lot number
- View all consolidated data for a lot
- See production records, quality inspections, shipping status
- Display summary statistics

#### 4. **📈 Production Analysis** - Issue Reporting
- Set date range (weekly, monthly, custom)
- View issues by production line
- Summary metrics (total issues, lines affected, quantities)
- Bar chart visualization

#### 5. **🐛 Defect Analysis** - Trend Visualization
- Select analysis period (7-90 days)
- Choose grouping (daily, weekly, monthly)
- View defect summary table
- Interactive line chart showing defect trends over time

#### 6. **📦 Shipment Status** - Status Tracking
- Search by Lot ID
- View shipment details (status, carrier, destination)
- Overall shipment summary with pie chart
- Status breakdown (Shipped, Pending, Not Shipped)

#### 7. **✅ Data Validation** - Quality Checks
- Run all consistency validation checks
- View discrepancy metrics
- List open discrepancies for review
- See validation details

#### 8. **📄 Report Generator** - Export Reports
- Choose report type (production issues, defect trends, shipment status)
- Select export format (JSON, CSV)
- Configure report parameters (date range for issues)
- Download generated reports
- Preview report content

#### 9. **ℹ️ About** - Documentation
- Project overview
- Feature descriptions
- Component architecture
- Performance metrics
- Support information

### Streamlit Features Used

- **File Upload**: Import CSV/Excel files directly
- **Metrics**: Display KPIs and statistics
- **DataFrames**: Interactive data tables
- **Charts**: Plotly visualizations (bar charts, line charts, pie charts)
- **Download Buttons**: Export reports to file
- **Sidebar Navigation**: Easy page switching
- **Session State**: Maintain application state between interactions
- **Spinners**: Show loading indicators
- **Alerts**: Display success/error/info messages

### Keyboard Shortcuts (in Streamlit)

- **R** - Rerun the app
- **C** - Clear cache
- **K** - Open Command Palette

### Tips for Using Streamlit

1. **Hot Reload**: Code changes automatically reload the app
2. **Session State**: Data persists during your session through the sidebar
3. **Caching**: Use `@st.cache_data` for expensive operations
4. **Performance**: Streamlit renders from top to bottom each interaction

---

## Project Files Comparison

### With pip (Original)
```
requirements.txt      ← List of dependencies and versions
venv/                 ← Manual virtual environment
```

### With Poetry (New)
```
pyproject.toml       ← Project configuration and dependencies (organized)
poetry.lock          ← Locked versions for reproducibility
.venv/               ← Automatic virtual environment (Poetry manages it)
```

### Benefits of Poetry

| Feature | pip + venv | Poetry |
|---------|-----------|--------|
| Version Locking | ❌ No | ✅ Yes (poetry.lock) |
| Dependency Groups | ❌ Multiple files | ✅ Built-in |
| Reproducibility | ⚠️ Manual | ✅ Automatic |
| Lock File | ❌ Manual | ✅ Automatic |
| Publish Package | ❌ Manual setup | ✅ One command |
| Virtual Env | ❌ Manual | ✅ Automatic |

---

## Quick Start with Poetry + Streamlit

```bash
# 1. Install Poetry (first time only)
pip install poetry

# 2. Install project dependencies
poetry install

# 3. Run Streamlit dashboard
poetry run streamlit run streamlit_app.py

# 4. Open browser to http://localhost:8501
```

---

## Running Tests with Poetry

```bash
# Run all tests
poetry run pytest test_suite.py -v

# Run with coverage
poetry run pytest test_suite.py --cov=. --cov-report=html

# Run specific test class
poetry run pytest test_suite.py::TestAC1MultiSourceImport -v

# View coverage report
# Open: htmlcov/index.html
```

---

## Troubleshooting Poetry

### Poetry Command Not Found
```bash
# Add Poetry to PATH (Windows)
$env:Path += ";$env:AppData\Python\Scripts"

# Or reinstall
pip install --user poetry
```

### Virtual Environment Issues
```bash
# Remove and reinstall
poetry env remove
poetry install

# Or use system Python
poetry env use python
```

### Lock File Conflicts
```bash
poetry lock --no-update
```

---

## Environment Variables with Poetry

Poetry will automatically load from `.env` using `python-dotenv`:

1. Create `.env` file in project root:
   ```ini
   DB_HOST=localhost
   DB_USER=postgres
   DB_PASSWORD=your_password
   ```

2. Used automatically by `config.py`

---

## Deployment Considerations

### Streamlit Cloud Deployment

1. Push project to GitHub
2. Go to https://streamlit.io/cloud
3. Create new app pointing to `streamlit_app.py`
4. Add secrets in Settings > Secrets management:
   ```
   DB_HOST = "your_host"
   DB_PASSWORD = "your_password"
   ```

### Docker Deployment

```dockerfile
FROM python:3.11
WORKDIR /app
RUN pip install poetry
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root
COPY . .
CMD ["poetry", "run", "streamlit", "run", "streamlit_app.py"]
```

---

## Additional Poetry Commands

```bash
# Show locked versions
poetry show

# Check for updates
poetry show --outdated

# Remove dependency
poetry remove package_name

# Create new project
poetry new my_project

# Initialize in existing directory
poetry init

# Build distribution
poetry build

# Publish to PyPI (if applicable)
poetry publish
```

---

## Summary

You now have:
- ✅ **Poetry Configuration** (`pyproject.toml`) with all dependencies
- ✅ **Streamlit Dashboard** (`streamlit_app.py`) with interactive UI
- ✅ **All features** from the original project, plus web interface
- ✅ **Automatic environment management** via Poetry
- ✅ **Easy deployment** ready for Streamlit Cloud or Docker

**Start exploring your data with:** `poetry run streamlit run streamlit_app.py`
