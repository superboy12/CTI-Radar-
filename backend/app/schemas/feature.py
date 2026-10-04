"""
Feature extraction schemas for website analysis.
"""
from typing import Dict, List, Optional
from pydantic import BaseModel

class WebsiteFeatures(BaseModel):
    """Extracted features from a website."""
    title: Optional[str] = None
    description: Optional[str] = None
    keywords: Optional[str] = None
    text_content: Optional[str] = None
    word_count: int = 0
    external_links: List[str] = []
    internal_links: List[str] = []
    has_login_form: bool = False
    has_registration_form: bool = False
    has_livechat_widget: bool = False
    suspicious_keywords_found: List[str] = []
    server: Optional[str] = None
    status_code: Optional[int] = None
    redirect_url: Optional[str] = None
    
    # === ASET DOMAIN (Footprinting Otomatis) ===
    # Domain dari gambar, GIF, animasi, script, iframe, video, dll.
    image_domains: List[str] = []       # Domain dari <img src>, background-image
    script_domains: List[str] = []      # Domain dari <script src>
    iframe_domains: List[str] = []      # Domain dari <iframe src>
    css_domains: List[str] = []         # Domain dari <link rel="stylesheet">
    media_domains: List[str] = []       # Domain dari <video>, <source>, <audio>
    all_referenced_domains: List[str] = []  # Gabungan semua domain unik yang ditemukan

class FeatureExtractionResponse(BaseModel):
    """Response containing extracted features."""
    domain_id: str
    domain: str
    features: WebsiteFeatures
    error: Optional[str] = None

class KeywordAnalysisRequest(BaseModel):
    """Request to analyze text against specific keywords."""
    keywords: List[str]
    threshold: float = 0.5
