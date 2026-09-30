"""
Seed data script - populates the database with sample data for development.

Usage:
    python -m scripts.seed_data

Note: Run this from the backend/ directory after the database is initialized.
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.session import AsyncSessionLocal
from app.models.domain import Domain
from app.models.infrastructure import IP, Nameserver, Certificate
from app.models.blocklist import ThreatSource
from sqlalchemy import select


SAMPLE_DOMAINS = [
    {"domain": "example.com", "source": "manual", "status": "analyzed", "classification": "LEGITIMATE", "confidence": 0.95, "risk_level": "LOW"},
    {"domain": "test-site.org", "source": "manual", "status": "analyzed", "classification": "LEGITIMATE", "confidence": 0.88, "risk_level": "LOW"},
    {"domain": "suspicious-domain.xyz", "source": "research", "status": "analyzed", "classification": "SUSPICIOUS", "confidence": 0.72, "risk_level": "MEDIUM"},
    {"domain": "unknown-site.net", "source": "research", "status": "pending"},
    {"domain": "sample-research.info", "source": "dataset", "status": "pending"},
    {"domain": "academic-test.edu", "source": "manual", "status": "analyzed", "classification": "LEGITIMATE", "confidence": 0.99, "risk_level": "LOW"},
    {"domain": "flagged-domain.club", "source": "research", "status": "analyzed", "classification": "GAMBLING_INDICATED", "confidence": 0.85, "risk_level": "HIGH"},
    {"domain": "review-pending.online", "source": "research", "status": "analyzing"},
]

SAMPLE_THREAT_SOURCES = [
    {"name": "Manual Input", "source_type": "manual", "description": "Domains manually submitted by researchers"},
    {"name": "Research Dataset", "source_type": "dataset", "description": "Domains from curated research datasets"},
    {"name": "Public Threat Feed", "source_type": "feed", "description": "Public threat intelligence feeds", "url": "https://example.com/feed"},
]


async def seed():
    """Seed the database with sample data."""
    async with AsyncSessionLocal() as session:
        # Check if already seeded
        result = await session.execute(select(Domain).limit(1))
        if result.scalar_one_or_none():
            print("Database already has data. Skipping seed.")
            return

        # Seed domains
        for data in SAMPLE_DOMAINS:
            domain = Domain(**data)
            session.add(domain)
        print(f"Seeded {len(SAMPLE_DOMAINS)} sample domains")

        # Seed threat sources
        for data in SAMPLE_THREAT_SOURCES:
            source = ThreatSource(**data)
            session.add(source)
        print(f"Seeded {len(SAMPLE_THREAT_SOURCES)} threat sources")

        await session.commit()
        print("Seed completed successfully!")


if __name__ == "__main__":
    asyncio.run(seed())
