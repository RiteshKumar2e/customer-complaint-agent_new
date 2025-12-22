# 🗄️ Database Setup Guide

## Database Configuration

The backend now supports both **SQLite (development)** and **PostgreSQL (production)**.

### Current Setup

**File**: `.env`
```
DATABASE_URL=postgresql://user:password@localhost:5432/complaints_db
```

## Option 1: SQLite (Local Development - Default)

No additional setup needed! SQLite works out of the box.

```python
# In app/db/database.py
DATABASE_URL = "sqlite:///./complaints.db"
```

**Pros**:
- No external database needed
- Perfect for local development
- File-based persistence
- Zero configuration

**File created**: `complaints.db` (auto-created on first run)

## Option 2: PostgreSQL (Production Recommended)

### Installation

1. **Install PostgreSQL**:
   ```bash
   # Windows (using Chocolatey)
   choco install postgresql

   # macOS
   brew install postgresql

   # Linux (Ubuntu/Debian)
   sudo apt-get install postgresql postgresql-contrib
   ```

2. **Start PostgreSQL**:
   ```bash
   # Windows
   pg_ctl -D "C:\Program Files\PostgreSQL\data" start

   # macOS
   brew services start postgresql

   # Linux
   sudo service postgresql start
   ```

3. **Create Database**:
   ```bash
   # Connect to PostgreSQL
   psql -U postgres

   # In psql shell:
   CREATE DATABASE complaints_db;
   CREATE USER complaint_user WITH PASSWORD 'secure_password';
   ALTER ROLE complaint_user SET client_encoding TO 'utf8';
   ALTER ROLE complaint_user SET default_transaction_isolation TO 'read committed';
   ALTER ROLE complaint_user SET default_transaction_deferrable TO on;
   ALTER ROLE complaint_user SET timezone TO 'UTC';
   GRANT ALL PRIVILEGES ON DATABASE complaints_db TO complaint_user;
   \q
   ```

4. **Update `.env`**:
   ```
   DATABASE_URL=postgresql://complaint_user:secure_password@localhost:5432/complaints_db
   ```

5. **Initialize Database**:
   ```bash
   python init_db.py
   ```

## Database Schema

### Complaints Table

```sql
CREATE TABLE complaints (
    id SERIAL PRIMARY KEY,
    complaint_text TEXT NOT NULL,
    category VARCHAR(50) NOT NULL,
    priority VARCHAR(20) NOT NULL,
    sentiment VARCHAR(20),
    response TEXT,
    solution TEXT,
    satisfaction_prediction VARCHAR(20),
    action VARCHAR(255),
    similar_complaints TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_resolved BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_complaints_category ON complaints(category);
CREATE INDEX idx_complaints_priority ON complaints(priority);
CREATE INDEX idx_complaints_created_at ON complaints(created_at);
```

## Fields Description

| Field | Type | Description |
|-------|------|-------------|
| `id` | INTEGER | Primary key |
| `complaint_text` | TEXT | Original complaint from user |
| `category` | VARCHAR(50) | Billing, Technical, Delivery, Service, Security |
| `priority` | VARCHAR(20) | High, Medium, Low |
| `sentiment` | VARCHAR(20) | Positive, Neutral, Negative, Angry |
| `response` | TEXT | AI-generated response |
| `solution` | TEXT | Proposed solution |
| `satisfaction_prediction` | VARCHAR(20) | Predicted satisfaction level |
| `action` | VARCHAR(255) | Recommended action |
| `similar_complaints` | TEXT | References to similar issues |
| `created_at` | TIMESTAMP | When complaint was created |
| `updated_at` | TIMESTAMP | When complaint was last updated |
| `is_resolved` | BOOLEAN | Resolution status |

## Running with Database

### Initialize Database (First Time Only)

```bash
cd backend
python init_db.py
```

Output:
```
🗄️  Initializing database...
📍 Using database: sqlite:///./complaints.db
📝 Creating tables...
✅ Database initialized successfully!

Tables created:
  • complaints - Stores customer complaints and AI analysis
```

### Start Backend

```bash
cd backend
uvicorn app.main:app --reload
```

The database tables will be created automatically on startup if they don't exist.

## Database Queries

### Get All Complaints

```bash
curl http://localhost:8000/complaints
```

Response:
```json
{
  "total": 5,
  "complaints": [
    {
      "id": 1,
      "complaint_text": "...",
      "category": "Billing",
      "priority": "High",
      "sentiment": "Angry",
      ...
    }
  ]
}
```

### Get Specific Complaint

```bash
curl http://localhost:8000/complaints/1
```

### Submit Complaint (Creates DB Entry)

```bash
curl -X POST http://localhost:8000/complaint \
  -H "Content-Type: application/json" \
  -d '{"complaint": "Your complaint text"}'
```

The complaint is automatically saved to the database with all AI analysis results.

## Switching Between Databases

### Use SQLite (Local Development)

Edit `app/db/database.py`:
```python
DATABASE_URL = "sqlite:///./complaints.db"
```

### Use PostgreSQL (Production)

Update `.env`:
```
DATABASE_URL=postgresql://user:password@localhost:5432/complaints_db
```

## Data Persistence

### SQLite
- Data stored in `complaints.db` file
- Persists across restarts
- No external service needed

### PostgreSQL
- Data stored in PostgreSQL server
- Professional grade persistence
- Supports concurrent access
- Better for production

## Backup & Restore

### SQLite Backup
```bash
cp complaints.db complaints.db.backup
```

### PostgreSQL Backup
```bash
pg_dump -U complaint_user complaints_db > backup.sql
```

### PostgreSQL Restore
```bash
psql -U complaint_user complaints_db < backup.sql
```

## Troubleshooting

### "Database does not exist"
- PostgreSQL: Run CREATE DATABASE command (see above)
- SQLite: Run `python init_db.py`

### "Connection refused"
- Check PostgreSQL is running
- Verify DATABASE_URL in `.env`
- Check port 5432 is accessible

### "Permission denied"
- Verify user credentials in DATABASE_URL
- Check user has correct GRANT permissions

### "Table does not exist"
- Run `python init_db.py` to create tables
- Check database connection is working

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/complaint` | POST | Submit complaint and store in DB |
| `/complaints` | GET | Get all complaints |
| `/complaints/{id}` | GET | Get specific complaint by ID |

## Environment Variables

```bash
# Database connection (SQLite or PostgreSQL)
DATABASE_URL=postgresql://user:password@localhost:5432/complaints_db

# Or for SQLite:
DATABASE_URL=sqlite:///./complaints.db

# API Key for Gemini
GEMINI_API_KEY=your_key_here

# Redis configuration
REDIS_HOST=localhost
REDIS_PORT=6379
```

---

**Status**: ✅ Database configured with SQL support!
