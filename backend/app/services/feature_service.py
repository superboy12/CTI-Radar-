"""
Website Feature Extraction Service (Playwright Upgraded).

Fetches website content by fully rendering Javascript, takes visual evidence (screenshots),
and extracts features (text, links, metadata) useful for ML classification.
"""
import os
import re
import asyncio
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse
from uuid import UUID
from concurrent.futures import ThreadPoolExecutor

from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from playwright.sync_api import sync_playwright

from app.core.logging import get_logger
from app.models.domain import Domain
from app.models.analysis import DomainAnalysis
from app.schemas.feature import WebsiteFeatures

logger = get_logger(__name__)

class FeatureExtractionService:
    """Service to extract website features using a Headless Browser."""

    SUSPICIOUS_KEYWORDS = [
        "judi", "slot", "gacor", "togel", "taruhan", "poker",
        "casino", "kasino", "deposit", "withdraw", "jackpot",
        "rtp", "bonus", "maxwin", "pragmatic", "sbobet", "toto", "wismatoto"
    ]

    def __init__(self, db: AsyncSession):
        self.db = db
        self.screenshots_dir = os.path.join(os.getcwd(), "screenshots")
        os.makedirs(self.screenshots_dir, exist_ok=True)

    def _run_playwright_sync(self, domain_name: str, domain_id: UUID) -> Dict[str, Any]:
        """Run playwright synchronously to avoid Windows asyncio loop conflicts."""
        from playwright_stealth import Stealth
        
        features = WebsiteFeatures()
        urls = [f"https://{domain_name}", f"http://{domain_name}"]
        content = None
        
        with sync_playwright() as p:
            # Mengaktifkan bypass tambahan untuk mengelabui Cloudflare
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"]
            )
            context = browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            Stealth().apply_stealth_sync(page) # Menerapkan siluman (stealth mode)
            
            for url in urls:
                try:
                    response = page.goto(url, timeout=30000, wait_until="domcontentloaded")
                    if response:
                        features.status_code = response.status
                        features.server = response.headers.get("server", "")
                    
                    page.wait_for_timeout(3000)
                    
                    screenshot_path = os.path.join(self.screenshots_dir, f"{domain_name}_{domain_id}.png")
                    page.screenshot(path=screenshot_path)
                    
                    content = page.content()
                    
                    final_url = page.url
                    if final_url != url and final_url != url + "/":
                        features.redirect_url = final_url
                        
                    break
                except Exception as e:
                    logger.warning("fetch_failed", url=url, error=str(e))
                    continue
                    
            browser.close()
            
        return {"content": content, "features": features}

    async def extract_features(self, domain_id: UUID, domain_name: str) -> Dict[str, Any]:
        logger.info("feature_extraction_start", domain=domain_name)
        
        error_msg = None
        
        # Run playwright in a separate thread to not block the async loop and avoid Windows NotImplementedError
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor() as pool:
            result = await loop.run_in_executor(pool, self._run_playwright_sync, domain_name, domain_id)
            
        content = result["content"]
        features = result["features"]

        if not content:
            error_msg = "Could not fetch or render content from domain"
            logger.error("feature_extraction_failed", domain=domain_name, error=error_msg)
            return {"features": features, "error": error_msg}

        # Parse HTML
        try:
            soup = BeautifulSoup(content, "lxml")
            
            if soup.title:
                features.title = soup.title.string.strip() if soup.title.string else None
                
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc and meta_desc.get("content"):
                features.description = meta_desc["content"].strip()

            for script in soup(["script", "style"]):
                script.extract()
            text = soup.get_text(separator=" ")
            text = re.sub(r'\s+', ' ', text).strip()
            
            features.text_content = text[:10000]
            features.word_count = len(text.split())

            text_lower = text.lower()
            features.suspicious_keywords_found = [
                kw for kw in self.SUSPICIOUS_KEYWORDS if kw in text_lower
            ]

            # Analyze Links
            for link in soup.find_all("a", href=True):
                href = link["href"].strip()
                if not href or href.startswith("javascript:") or href.startswith("mailto:"):
                    continue
                
                parsed_href = urlparse(href)
                if not parsed_href.netloc or domain_name in parsed_href.netloc:
                    if len(features.internal_links) < 50:
                        features.internal_links.append(href)
                else:
                    if len(features.external_links) < 50:
                        features.external_links.append(href)

            # Look for forms
            forms = soup.find_all("form")
            for form in forms:
                form_action = form.get("action", "").lower()
                inputs = form.find_all("input")
                input_names = [i.get("name", "").lower() for i in inputs]
                input_types = [i.get("type", "").lower() for i in inputs]
                
                if "password" in input_types:
                    features.has_login_form = True
                
                if "register" in form_action or "signup" in form_action or "daftar" in form_action:
                    features.has_registration_form = True
                elif len(inputs) > 3 and "email" in input_types and "password" in input_types:
                    features.has_registration_form = True
                    
        except Exception as e:
            error_msg = f"Error parsing HTML: {str(e)}"
            logger.error("parse_failed", domain=domain_name, error=error_msg)

        # Store in Database
        try:
            analysis = DomainAnalysis(
                domain_id=domain_id,
                analysis_type="feature_extraction",
                website_features=features.model_dump(),
                status="completed" if not error_msg else "error",
                error_message=error_msg
            )
            self.db.add(analysis)
            
            if len(features.suspicious_keywords_found) >= 1:
                result = await self.db.execute(select(Domain).where(Domain.id == domain_id))
                domain = result.scalar_one_or_none()
                if domain and domain.status == "analyzed" and not domain.classification:
                    domain.classification = "GAMBLING_INDICATED"
                    domain.risk_level = "HIGH"
                    domain.notes = f"Auto-flagged (Playwright): Found {len(features.suspicious_keywords_found)} keywords."
            
            await self.db.commit()
        except Exception as e:
            logger.error("db_store_failed", domain=domain_name, error=str(e))
            await self.db.rollback()

        logger.info("feature_extraction_complete", domain=domain_name, word_count=features.word_count)
        return {"features": features, "error": error_msg}
