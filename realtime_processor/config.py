from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel

class SeverityLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ALERT = "alert"
    CRITICAL = "critical"

class ThresholdConfig(BaseModel):
    value: float
    severity: SeverityLevel
    description: str

class PM25Thresholds:
    # WHO Guidelines
    WHO_24H: ThresholdConfig = ThresholdConfig(
        value=15.0,
        severity=SeverityLevel.ALERT,
        description="WHO 24-hour guideline"
    )
    WHO_ANNUAL: ThresholdConfig = ThresholdConfig(
        value=5.0,
        severity=SeverityLevel.WARNING,
        description="WHO annual guideline"
    )

    # EPA Standards
    EPA_24H: ThresholdConfig = ThresholdConfig(
        value=35.0,
        severity=SeverityLevel.CRITICAL,
        description="EPA 24-hour standard"
    )
    EPA_ANNUAL: ThresholdConfig = ThresholdConfig(
        value=12.0,
        severity=SeverityLevel.ALERT,
        description="EPA annual standard"
    )

    # EU Standards
    EU_24H: ThresholdConfig = ThresholdConfig(
        value=25.0,
        severity=SeverityLevel.ALERT,
        description="EU 24-hour standard"
    )
    EU_ANNUAL: ThresholdConfig = ThresholdConfig(
        value=20.0,
        severity=SeverityLevel.WARNING,
        description="EU annual standard"
    )

    @classmethod
    def get_all_thresholds(cls) -> List[ThresholdConfig]:
        return [
            cls.WHO_24H,
            cls.WHO_ANNUAL,
            cls.EPA_24H,
            cls.EPA_ANNUAL,
            cls.EU_24H,
            cls.EU_ANNUAL
        ]

    @classmethod
    def get_threshold_for_value(cls, value: float) -> Optional[ThresholdConfig]:
        """Returns the highest severity threshold that the value exceeds."""
        exceeded_thresholds = [
            t for t in cls.get_all_thresholds()
            if value >= t.value
        ]
        return max(exceeded_thresholds, key=lambda t: t.value) if exceeded_thresholds else None 