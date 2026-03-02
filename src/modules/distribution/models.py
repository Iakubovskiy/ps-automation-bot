"""Re-export domain models so Django can discover them for migrations."""
from modules.distribution.domain.distribution_driver import DistributionDriver  # noqa: F401
from modules.distribution.domain.distribution_manifest import DistributionManifest  # noqa: F401
