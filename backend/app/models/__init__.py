"""
Models package - imports all models to ensure they are registered with SQLAlchemy.
"""
from app.models.base import Base
from app.models.user import User
from app.models.domain import Domain
from app.models.infrastructure import (
    IP, Nameserver, Certificate,
    DomainIP, DomainNameserver, DomainCertificate,
)
from app.models.analysis import DomainAnalysis, ScanJob
from app.models.ml import Dataset, MLModel, Experiment, MLPrediction
from app.models.alert import Alert
from app.models.blocklist import BlocklistEntry, FilterPolicy, ThreatSource
from app.models.audit import AuditLog

__all__ = [
    "Base",
    "User",
    "Domain",
    "IP", "Nameserver", "Certificate",
    "DomainIP", "DomainNameserver", "DomainCertificate",
    "DomainAnalysis", "ScanJob",
    "Dataset", "MLModel", "Experiment", "MLPrediction",
    "Alert",
    "BlocklistEntry", "FilterPolicy", "ThreatSource",
    "AuditLog",
]
