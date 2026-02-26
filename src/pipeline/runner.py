"""End-to-end pipeline orchestrator.

Runs the full MenuLens pipeline: discover -> fetch -> extract -> normalize.
Each step is idempotent — safe to re-run.
"""

from src.common.logger import get_logger, setup_logging
from src.common.models import GeoPoint
from src.config.settings import get_settings
from src.db.engine import create_engine
from src.discovery.google_maps import GoogleMapsClient
from src.discovery.models import DiscoveryRequest
from src.discovery.service import DiscoveryService
from src.extraction.model_client import ExtractionModelClient
from src.extraction.service import ExtractionService
from src.fetching.service import FetchingService
from src.normalization.service import NormalizationService

logger = get_logger(__name__)


async def run_pipeline(
    latitude: float,
    longitude: float,
    radius_miles: int = 5,
    cuisine: str = "indian",
) -> dict[str, object]:
    """Run the full MenuLens pipeline for a location.

    Steps:
    1. Discovery — find restaurants via Google Maps
    2. Fetching — retrieve menu content from discovered URLs
    3. Extraction — extract structured data using LLM
    4. Normalization — match dish names to canonical taxonomy

    Each step is idempotent. Already-processed items are skipped.

    Args:
        latitude: Center point latitude.
        longitude: Center point longitude.
        radius_miles: Search radius.
        cuisine: Target cuisine type.

    Returns:
        Dict with statistics from each pipeline stage.
    """
    setup_logging(json_output=False, log_level="INFO")
    settings = get_settings()
    _engine, session_factory = create_engine(settings)

    results: dict[str, object] = {}

    async with session_factory() as session:
        # Step 1: Discovery
        logger.info("pipeline_step", step="discovery")
        google_client = GoogleMapsClient(settings.google_maps_api_key)
        discovery_service = DiscoveryService(google_client, session)

        discovery_result = await discovery_service.discover(
            DiscoveryRequest(
                location=GeoPoint(latitude=latitude, longitude=longitude),
                radius_miles=radius_miles,
                cuisine=cuisine,
                max_results=settings.discovery_max_results,
            )
        )
        await google_client.close()

        results["discovery"] = {
            "total_found": discovery_result.total_found,
            "with_websites": discovery_result.total_with_websites,
        }

        # Step 2: Fetching
        logger.info("pipeline_step", step="fetching")
        fetching_service = FetchingService(session, settings)
        fetch_stats = await fetching_service.fetch_all_pending()
        results["fetching"] = fetch_stats

        # Step 3: Extraction
        logger.info("pipeline_step", step="extraction")
        model_client = ExtractionModelClient(settings)
        extraction_service = ExtractionService(model_client, session, settings)
        extraction_stats = await extraction_service.extract_all_pending()
        results["extraction"] = extraction_stats

        # Step 4: Normalization
        logger.info("pipeline_step", step="normalization")
        normalization_service = NormalizationService(session)
        await normalization_service.seed_taxonomy(cuisine)
        normalization_stats = await normalization_service.normalize_all_unmatched()
        results["normalization"] = normalization_stats

    logger.info("pipeline_completed", results=results)
    return results
