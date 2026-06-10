# Career Manager 🎯

A technical system for managing executive job applications, focusing on data persistence, multi-language support, and automated document generation.

## Technical Overview

Career Manager is built to centralize professional narratives and application tracking. It leverages a relational database to maintain consistency across different job applications and languages (English, Spanish, French).

### Key Technical Features
- **Relational Data Persistence**: Structured storage for company types, target organizations, and granular application details.
- **Dynamic Document Generation**: Utilizes Word templates with smart placeholders (e.g., `{job}`, `{skills}`) powered by PostgreSQL data.
- **Multi-language Schema**: Native support for managing content across three languages within the same application context.
- **Streamlit Interface**: A web-based CRUD interface for efficient data entry and management, reducing manual SQL operations.

---

## Getting Started

### Prerequisites
- **Python**: 3.8+
- **Database**: PostgreSQL 17 (Required for compatibility with current DDL and triggers)
- **Environment Management**: `pip` or `uv` recommended

### Installation

```bash
# Clone the repository
git clone https://github.com/armjorge/career_manager.git
cd career_manager

# Install dependencies
pip install -r requirements.txt

# Environment Setup
cp .env.example .env
```

### Configuration

The application requires a `DB_URL` environment variable. Configure it in your `.env` file:

```bash
DB_URL=postgresql://user:password@server:port/database
```

---

## System Architecture

### Project Structure
```
career_manager/
├── carrier_management.py      # Main orchestrator / Entry point
├── Library/
│   ├── SQL_initialize.py      # Database schema setup logic
│   ├── SQL_management.py      # Connection pooling and query management
│   ├── CV_generation.py       # Document generation engine (Word)
│   ├── concept_filing.py      # Streamlit UI implementation
│   └── db_utils.py            # Low-level database utilities
├── SQL/                       # DDL and Database Scripts
│   ├── ddl_postgres17.sql     # Core schema definition
│   ├── ddl_postgres17_metadata.sql # Metadata and auxiliary objects
│   └── initializing.sql       # Initial setup and seeding
├── config/
│   └── config.yml             # System and DB configuration
└── Data Model/                # Interactive documentation
    └── index.html             # Luna Modeler HTML Report
```

### Database & Schema
The system relies on a PostgreSQL 17 schema. The scripts located in the `/SQL` directory are responsible for recreating the entire environment, including tables, sequences, and triggers.

- **`dim_company`**: Dimension table for target organizations.
- **`fact_application`**: Central transaction table for job applications.
- **`dim_tracker`**: Application status and lifecycle tracking.

### Data Model Visualization
The following diagram represents the core entity-relationship structure:

![Data Model](images/data_model.png)

For a detailed technical exploration, see the [Interactive Data Model Report](Data%20Model/index.html).

---

## Development Workflow

1.  **Initialization**: Run the orchestrator to initialize the PostgreSQL schema.
2.  **Data Ingestion**: Use the Streamlit interface to populate dimensions and facts.
3.  **Generation**: Trigger the Word engine to merge database records with professional templates.

## License
MIT License
