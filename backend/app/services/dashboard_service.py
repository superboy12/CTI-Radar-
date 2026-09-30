"""
Dashboard and Threat Intelligence Service.

Aggregates data for frontend dashboards and reports.
"""
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.domain import Domain
from app.schemas.dashboard import (
    DashboardStatsResponse,
    RiskDistribution,
    ClassificationDistribution,
    ThreatTrendItem
)

logger = get_logger(__name__)

class DashboardService:
    """Service for generating dashboard statistics."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_stats(self) -> DashboardStatsResponse:
        """Get high-level statistics for the dashboard."""
        logger.info("generating_dashboard_stats")
        
        # 1. Basic Counts
        total_domains_result = await self.db.execute(select(func.count(Domain.id)))
        total_domains = total_domains_result.scalar_one()
        
        analyzed_domains_result = await self.db.execute(
            select(func.count(Domain.id)).where(Domain.status == "analyzed")
        )
        analyzed_domains = analyzed_domains_result.scalar_one()
        
        high_risk_result = await self.db.execute(
            select(func.count(Domain.id)).where(Domain.risk_level == "HIGH")
        )
        high_risk_domains = high_risk_result.scalar_one()

        # 2. Risk Distribution
        risk_dist = RiskDistribution()
        risk_query = await self.db.execute(
            select(Domain.risk_level, func.count(Domain.id))
            .where(Domain.risk_level.is_not(None))
            .group_by(Domain.risk_level)
        )
        for row in risk_query:
            level, count = row
            if level == "HIGH": risk_dist.high = count
            elif level == "MEDIUM": risk_dist.medium = count
            elif level == "LOW": risk_dist.low = count

        # 3. Classification Distribution
        class_dist = ClassificationDistribution()
        class_query = await self.db.execute(
            select(Domain.classification, func.count(Domain.id))
            .where(Domain.classification.is_not(None))
            .group_by(Domain.classification)
        )
        
        # Also get pending count (domains with no classification yet)
        pending_query = await self.db.execute(
            select(func.count(Domain.id)).where(Domain.classification.is_(None))
        )
        class_dist.pending = pending_query.scalar_one()

        for row in class_query:
            classification, count = row
            if classification == "GAMBLING_INDICATED": class_dist.gambling_indicated = count
            elif classification == "LEGITIMATE": class_dist.legitimate = count
            elif classification == "SUSPICIOUS": class_dist.suspicious = count
            else: class_dist.unknown += count

        # 4. Trend Analysis (Last 7 days of analyzed GAMBLING domains)
        # Note: SQLite datetime handling is tricky, so we do simple string matching or python side grouping for MVP
        today = datetime.now(timezone.utc).date()
        trend_items = []
        
        # We fetch all gambling domains and group in python to avoid SQL dialect issues between SQLite/Postgres
        trend_query = await self.db.execute(
            select(Domain.created_at)
            .where(Domain.classification == "GAMBLING_INDICATED")
        )
        
        # Initialize last 7 days with 0
        date_counts = {}
        for i in range(6, -1, -1):
            d = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            date_counts[d] = 0
            
        for row in trend_query:
            created_at = row[0]
            if created_at:
                date_str = created_at.date().strftime("%Y-%m-%d")
                if date_str in date_counts:
                    date_counts[date_str] += 1
                    
        for date_str, count in date_counts.items():
            trend_items.append(ThreatTrendItem(date=date_str, count=count))

        return DashboardStatsResponse(
            total_domains=total_domains,
            analyzed_domains=analyzed_domains,
            high_risk_domains=high_risk_domains,
            risk_distribution=risk_dist,
            classification_distribution=class_dist,
            recent_threats_trend=trend_items
        )

    async def get_recent_activity(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recently added or analyzed domains."""
        result = await self.db.execute(
            select(Domain)
            .order_by(desc(Domain.updated_at))
            .limit(limit)
        )
        domains = result.scalars().all()
        
        return [
            {
                "domain": d.domain,
                "status": d.status,
                "classification": d.classification,
                "risk_level": d.risk_level,
                "analyzed_at": d.updated_at
            }
            for d in domains
        ]
