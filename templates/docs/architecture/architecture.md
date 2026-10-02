# System Architecture


---

## Overview

```mermaid
graph TB
    Client[Client] --> API[API Server]
    API --> DB[(PostgreSQL)]
    API --> Cache[(Redis)]
    API --> Queue[Celery]
    Queue --> Worker[Worker]
    Worker --> DB
```

---

## Components

| Component | Purpose | Technology |
|-----------|---------|------------|
| API | HTTP endpoints | FastAPI |
| Database | Persistent storage | PostgreSQL |
| Cache | Session/caching | Redis |
| Queue | Async tasks | Celery |

---

## Data Flow

{Describe key data flows}

---

## External Dependencies

| Service | Purpose | Failure Impact |
|---------|---------|----------------|
| {Service} | {Purpose} | {What happens if down} |
