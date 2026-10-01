"""
Sibling Detection & Footprinting Service.

Ketika AI memvonis sebuah domain sebagai GAMBLING_INDICATED,
service ini secara otomatis:
1. Melakukan DNS footprinting (resolve IP & NS)
2. Mencari domain lain yang berbagi infrastruktur (IP/NS yang sama)
3. Menandai domain "saudara" sebagai SUSPICIOUS
4. Mengantrekan domain saudara untuk di-scan AI secara otomatis
5. Memperluas daftar kata kunci secara dinamis (TF-IDF)
"""
import re
import uuid
import datetime
from collections import Counter
from typing import Dict, Any, List, Optional, Set

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.domain import Domain
from app.models.infrastructure import (
    IP, Nameserver, DomainIP, DomainNameserver
)
from app.models.analysis import DomainAnalysis
from app.services.dns_service import DNSService
from app.services.infrastructure_service import InfrastructureService

logger = get_logger(__name__)


class SiblingDetectionService:
    """
    Service untuk mendeteksi domain 'saudara' dari situs judi
    dan memperluas kata kunci deteksi secara otomatis.
    """

    # Kata kunci dasar yang sudah kita miliki (baseline)
    BASELINE_KEYWORDS = {
        "judi", "slot", "gacor", "togel", "taruhan", "poker",
        "casino", "kasino", "deposit", "withdraw", "jackpot",
        "rtp", "bonus", "maxwin", "pragmatic", "sbobet", "toto", "wismatoto"
    }

    # Kata-kata yang TIDAK BOLEH dijadikan keyword (terlalu umum)
    STOPWORDS = {
        "the", "and", "for", "are", "but", "not", "you", "all",
        "can", "had", "her", "was", "one", "our", "out", "yang",
        "dan", "ini", "itu", "dengan", "untuk", "dari", "pada",
        "adalah", "akan", "juga", "sudah", "ada", "kami", "kita",
        "anda", "mereka", "bisa", "hanya", "lebih", "atau", "agar",
        "online", "game", "play", "home", "login", "register",
        "daftar", "masuk", "akun", "situs", "link", "alternatif",
        "www", "com", "net", "org", "http", "https", "loading",
        "just", "moment", "please", "wait", "error", "page",
    }

    def __init__(self, db: AsyncSession):
        self.db = db

    async def footprint_and_hunt(self, domain_id: uuid.UUID) -> Dict[str, Any]:
        """
        Footprinting utama: Setelah sebuah domain divonis GAMBLING_INDICATED,
        jalankan fungsi ini untuk memburu seluruh keluarganya.

        Returns:
            Dict berisi daftar sibling yang ditemukan dan keyword baru.
        """
        logger.info("sibling_hunt_start", domain_id=str(domain_id))

        # 1. Ambil info domain yang sudah divonis
        result = await self.db.execute(select(Domain).where(Domain.id == domain_id))
        source_domain = result.scalar_one_or_none()
        if not source_domain:
            return {"error": "Domain not found"}

        if source_domain.classification != "GAMBLING_INDICATED":
            return {"error": "Domain is not classified as GAMBLING_INDICATED", "skipped": True}

        # 2. Lakukan DNS Footprinting (resolve IP & NS, simpan ke DB)
        dns_svc = DNSService(self.db)
        try:
            dns_data = await dns_svc.resolve_and_store(domain_id, source_domain.domain)
            await self.db.commit()
            logger.info("footprint_dns_complete",
                        domain=source_domain.domain,
                        ips=len(dns_data.get("stored", {}).get("ips", [])),
                        ns=len(dns_data.get("stored", {}).get("nameservers", [])))
        except Exception as e:
            logger.warning("footprint_dns_failed", domain=source_domain.domain, error=str(e))
            dns_data = {"stored": {"ips": [], "nameservers": []}}

        # 3. Cari domain saudara yang berbagi infrastruktur
        infra_svc = InfrastructureService(self.db)
        siblings_data = await infra_svc.find_shared_infrastructure(domain_id)
        siblings = siblings_data.get("related_domains", [])

        # 4. Tandai sibling yang belum dianalisis sebagai SUSPICIOUS
        flagged_siblings = []
        for sibling in siblings:
            sibling_id = uuid.UUID(sibling["id"])

            # Skip jika sudah punya klasifikasi
            if sibling.get("classification") in ["GAMBLING_INDICATED", "LEGITIMATE"]:
                continue

            # Update domain sibling menjadi SUSPICIOUS
            sib_result = await self.db.execute(select(Domain).where(Domain.id == sibling_id))
            sib_domain = sib_result.scalar_one_or_none()
            if sib_domain and sib_domain.classification != "GAMBLING_INDICATED":
                sib_domain.classification = "SUSPICIOUS"
                sib_domain.risk_level = "MEDIUM"
                sib_domain.notes = (
                    f"Auto-flagged: Berbagi infrastruktur dengan {source_domain.domain} "
                    f"(GAMBLING_INDICATED). Shared IPs: {sibling.get('shared_ips', [])}, "
                    f"Shared NS: {sibling.get('shared_nameservers', [])}. "
                    f"Relationship strength: {sibling.get('relationship_strength', 0)}"
                )
                flagged_siblings.append({
                    "domain": sib_domain.domain,
                    "id": str(sib_domain.id),
                    "shared_ips": sibling.get("shared_ips", []),
                    "shared_ns": sibling.get("shared_nameservers", []),
                    "strength": sibling.get("relationship_strength", 0),
                })
                logger.info("sibling_flagged",
                            source=source_domain.domain,
                            sibling=sib_domain.domain,
                            strength=sibling.get("relationship_strength", 0))

        await self.db.commit()

        # 5. Ekspansi kata kunci dinamis
        new_keywords = await self._expand_keywords()

        result = {
            "source_domain": source_domain.domain,
            "source_classification": source_domain.classification,
            "dns_footprint": {
                "ips_found": len(dns_data.get("stored", {}).get("ips", [])),
                "ns_found": len(dns_data.get("stored", {}).get("nameservers", [])),
            },
            "siblings_found": len(siblings),
            "siblings_flagged_suspicious": len(flagged_siblings),
            "flagged_siblings": flagged_siblings,
            "dynamic_keywords": {
                "new_keywords_discovered": new_keywords,
                "total_keywords": len(self.BASELINE_KEYWORDS) + len(new_keywords),
            },
        }

        logger.info("sibling_hunt_complete",
                     domain=source_domain.domain,
                     siblings_found=len(siblings),
                     siblings_flagged=len(flagged_siblings),
                     new_keywords=len(new_keywords))

        return result

    async def _expand_keywords(self) -> List[str]:
        """
        TF-IDF sederhana: Mengumpulkan teks dari semua situs GAMBLING_INDICATED,
        menemukan kata-kata yang sangat sering muncul di situs judi
        tapi TIDAK muncul di situs aman, lalu menambahkannya ke keyword list.
        """
        # Ambil semua teks dari situs GAMBLING
        gambling_result = await self.db.execute(
            select(DomainAnalysis.website_features)
            .join(Domain, DomainAnalysis.domain_id == Domain.id)
            .where(
                Domain.classification == "GAMBLING_INDICATED",
                DomainAnalysis.analysis_type == "feature_extraction",
                DomainAnalysis.status == "completed",
                DomainAnalysis.website_features.isnot(None),
            )
        )

        gambling_word_counter = Counter()
        gambling_doc_count = 0

        for (features,) in gambling_result.all():
            if features and features.get("text_content"):
                text = features["text_content"].lower()
                # Hanya ambil kata yang bermakna (3-15 karakter, alfanumerik)
                words = set(re.findall(r'\b[a-z]{3,15}\b', text))
                words -= self.STOPWORDS
                words -= self.BASELINE_KEYWORDS
                gambling_word_counter.update(words)
                gambling_doc_count += 1

        if gambling_doc_count < 2:
            # Butuh minimal 2 situs judi untuk analisis yang bermakna
            return []

        # Ambil semua teks dari situs LEGITIMATE
        legit_result = await self.db.execute(
            select(DomainAnalysis.website_features)
            .join(Domain, DomainAnalysis.domain_id == Domain.id)
            .where(
                Domain.classification == "LEGITIMATE",
                DomainAnalysis.analysis_type == "feature_extraction",
                DomainAnalysis.status == "completed",
                DomainAnalysis.website_features.isnot(None),
            )
        )

        legit_words = set()
        for (features,) in legit_result.all():
            if features and features.get("text_content"):
                text = features["text_content"].lower()
                legit_words.update(re.findall(r'\b[a-z]{3,15}\b', text))

        # Temukan kata yang muncul di >=50% situs judi, tapi JARANG di situs aman
        min_frequency = max(2, gambling_doc_count // 2)  # Minimal muncul di 50% situs judi
        new_keywords = []

        for word, count in gambling_word_counter.most_common(100):
            if count >= min_frequency and word not in legit_words:
                new_keywords.append(word)

            if len(new_keywords) >= 20:  # Batasi 20 keyword baru per siklus
                break

        if new_keywords:
            logger.info("keywords_expanded",
                        new_keywords=new_keywords[:10],
                        total_new=len(new_keywords))

        return new_keywords

    async def get_dynamic_keywords(self) -> Dict[str, Any]:
        """
        Mengembalikan gabungan kata kunci baseline + kata kunci dinamis.
        Bisa dipanggil oleh FeatureExtractionService untuk mengupdate daftar keyword-nya.
        """
        new_keywords = await self._expand_keywords()

        combined = list(self.BASELINE_KEYWORDS | set(new_keywords))
        combined.sort()

        return {
            "baseline_keywords": sorted(list(self.BASELINE_KEYWORDS)),
            "discovered_keywords": sorted(new_keywords),
            "combined_keywords": combined,
            "total": len(combined),
        }

    async def get_hunting_report(self) -> Dict[str, Any]:
        """
        Laporan lengkap tentang hasil berburu domain saudara.
        Cocok untuk ditampilkan di dashboard.
        """
        # Hitung domain per klasifikasi
        stats_result = await self.db.execute(
            select(Domain.classification, func.count(Domain.id))
            .group_by(Domain.classification)
        )
        classification_stats = {row[0] or "UNCLASSIFIED": row[1] for row in stats_result.all()}

        # Hitung domain yang memiliki sibling
        # (domain yang berbagi IP dengan domain lain)
        shared_ip_result = await self.db.execute(
            select(IP.address, func.count(DomainIP.domain_id.distinct()))
            .join(DomainIP, IP.id == DomainIP.ip_id)
            .group_by(IP.address)
            .having(func.count(DomainIP.domain_id.distinct()) > 1)
        )
        shared_ips = [
            {"ip": row[0], "domain_count": row[1]}
            for row in shared_ip_result.all()
        ]

        # Ambil keyword dinamis
        keywords = await self.get_dynamic_keywords()

        return {
            "classification_stats": classification_stats,
            "shared_infrastructure": {
                "ips_with_multiple_domains": len(shared_ips),
                "details": shared_ips[:20],  # Top 20
            },
            "dynamic_keywords": keywords,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
