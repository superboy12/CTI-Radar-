"""
Machine Learning API schemas.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

class PredictionRequest(BaseModel):
    """Request to generate a prediction for a domain."""
    domain_id: str
    model_id: Optional[str] = None

class PredictionResponse(BaseModel):
    """Prediction result."""
    domain_id: str
    domain: str
    classification: str
    confidence: float
    risk_level: str
    prediction_id: str
    features_used: Dict[str, Any]

class TrainRequest(BaseModel):
    """Request to train a new model."""
    dataset_id: Optional[str] = None
    algorithm: str = "random_forest"
    hyperparameters: Optional[Dict[str, Any]] = None

class TrainResponse(BaseModel):
    """Result of a training job."""
    model_id: str
    name: str
    algorithm: str
    version: str
    metrics: Dict[str, float]

class ModelResponse(BaseModel):
    """Machine Learning model info."""
    id: str
    name: str
    algorithm: str
    version: str
    status: str
    trained_at: Optional[str] = None
