from typing import List, Dict, Any
from app.services.db_adapter import db


def get_departments() -> List[Dict[str, Any]]:
    """Retrieve all available academic departments."""
    depts = db.select_all("departments")
    if not depts:
        # Fallback to standard verified departments if not seeded yet
        default_depts = [
            {"id": "d1000000-0000-0000-0000-000000000001", "name": "Computer Science & Engineering", "created_at": "2026-01-01T00:00:00Z"},
            {"id": "d1000000-0000-0000-0000-000000000002", "name": "Information Technology", "created_at": "2026-01-01T00:00:00Z"},
            {"id": "d1000000-0000-0000-0000-000000000003", "name": "Electrical & Electronics Engineering", "created_at": "2026-01-01T00:00:00Z"},
            {"id": "d1000000-0000-0000-0000-000000000004", "name": "Electronics & Communication Engineering", "created_at": "2026-01-01T00:00:00Z"},
            {"id": "d1000000-0000-0000-0000-000000000005", "name": "Mechanical Engineering", "created_at": "2026-01-01T00:00:00Z"},
            {"id": "d1000000-0000-0000-0000-000000000006", "name": "Data Science & Artificial Intelligence", "created_at": "2026-01-01T00:00:00Z"},
        ]
        for d in default_depts:
            db.insert("departments", d)
        return db.select_all("departments")
    return depts


def get_skills() -> List[Dict[str, Any]]:
    """Retrieve all available technical and domain skills."""
    skills = db.select_all("skills")
    if not skills:
        default_skills = [
            {"id": "a1000000-0000-0000-0000-000000000001", "name": "Python", "category": "ai_ml", "created_at": "2026-01-01T00:00:00Z"},
            {"id": "a1000000-0000-0000-0000-000000000002", "name": "PyTorch", "category": "ai_ml", "created_at": "2026-01-01T00:00:00Z"},
            {"id": "a1000000-0000-0000-0000-000000000003", "name": "TensorFlow", "category": "ai_ml", "created_at": "2026-01-01T00:00:00Z"},
            {"id": "a1000000-0000-0000-0000-000000000004", "name": "React", "category": "frontend", "created_at": "2026-01-01T00:00:00Z"},
            {"id": "a1000000-0000-0000-0000-000000000005", "name": "TypeScript", "category": "frontend", "created_at": "2026-01-01T00:00:00Z"},
            {"id": "a1000000-0000-0000-0000-000000000006", "name": "FastAPI", "category": "backend", "created_at": "2026-01-01T00:00:00Z"},
            {"id": "a1000000-0000-0000-0000-000000000007", "name": "PostgreSQL", "category": "backend", "created_at": "2026-01-01T00:00:00Z"},
            {"id": "a1000000-0000-0000-0000-000000000008", "name": "Docker", "category": "cloud_devops", "created_at": "2026-01-01T00:00:00Z"},
            {"id": "a1000000-0000-0000-0000-000000000009", "name": "Machine Learning", "category": "ai_ml", "created_at": "2026-01-01T00:00:00Z"},
            {"id": "a1000000-0000-0000-0000-000000000010", "name": "Deep Learning", "category": "ai_ml", "created_at": "2026-01-01T00:00:00Z"},
            {"id": "a1000000-0000-0000-0000-000000000011", "name": "Computer Vision", "category": "ai_ml", "created_at": "2026-01-01T00:00:00Z"},
            {"id": "a1000000-0000-0000-0000-000000000012", "name": "NLP", "category": "ai_ml", "created_at": "2026-01-01T00:00:00Z"},
            {"id": "a1000000-0000-0000-0000-000000000013", "name": "SQL", "category": "backend", "created_at": "2026-01-01T00:00:00Z"},
            {"id": "a1000000-0000-0000-0000-000000000014", "name": "Pandas", "category": "data_science", "created_at": "2026-01-01T00:00:00Z"},
        ]
        for s in default_skills:
            db.insert("skills", s)
        return db.select_all("skills")
    return skills


def get_interests() -> List[Dict[str, Any]]:
    """Retrieve all available project domain interests."""
    interests = db.select_all("interests")
    if not interests:
        default_interests = [
            {"id": "b1000000-0000-0000-0000-000000000001", "name": "Artificial Intelligence & Deep Learning", "created_at": "2026-01-01T00:00:00Z"},
            {"id": "b1000000-0000-0000-0000-000000000002", "name": "Web Development & Cloud Computing", "created_at": "2026-01-01T00:00:00Z"},
            {"id": "b1000000-0000-0000-0000-000000000003", "name": "Robotics & Autonomous Systems", "created_at": "2026-01-01T00:00:00Z"},
            {"id": "b1000000-0000-0000-0000-000000000004", "name": "Cybersecurity & Cryptography", "created_at": "2026-01-01T00:00:00Z"},
        ]
        for i in default_interests:
            db.insert("interests", i)
        return db.select_all("interests")
    return interests
