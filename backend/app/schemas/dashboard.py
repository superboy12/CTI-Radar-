"""
Dashboard and Threat Intelligence API schemas.
"""
from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel

class RiskDistribution(BaseModel):
    """Distribution of domains by risk level."""
    high: int = 0
    medium: int = 0
    low: int = 0

class ClassificationDistribution(BaseModel):
    """Distribution of domains by classification."""
    gambling_indicated: int = 0
    legitimate: int = 0
    suspicious: int = 0
    pending: int = 0
    unknown: int = 0

class ThreatTrendItem(BaseModel):
    """A data point for threat trends over time."""
    date: str
    count: int

class DashboardStatsResponse(BaseModel):
    """Comprehensive dashboard statistics."""
    total_domains: int
    analyzed_domains: int
    high_risk_domains: int
    risk_distribution: RiskDistribution
    classification_distribution: ClassificationDistribution
    recent_threats_trend: List[ThreatTrendItem] = []

class RecentActivityResponse(BaseModel):
    """Recent domain analysis activity."""
    domain: str
    status: str
    classification: Optional[str]
    risk_level: Optional[str]
    analyzed_at: Optional[datetime]
