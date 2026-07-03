"""Alert rules engine — Module 10."""

from dataclasses import dataclass
from enum import Enum


class AlertType(str, Enum):
    HOTSPOT_NEARBY = "hotspot_nearby"
    HIGH_RISK_AREA = "high_risk_area"
    AVOID_AREA = "avoid_area"
    SPRAY_SCHEDULE = "spray_schedule"
    DISEASE_AWARENESS = "disease_awareness"


@dataclass
class AlertContext:
    ward_code: str
    ward_name: str
    risk_score: float
    outbreak_probability_15d: float
    language: str = "hi_IN"


THRESHOLDS = {
    AlertType.HIGH_RISK_AREA: 75.0,
    AlertType.AVOID_AREA: 85.0,
}


def evaluate_alerts(ctx: AlertContext) -> list[AlertType]:
    """Determine which alerts to fire for a ward prediction."""
    alerts: list[AlertType] = []
    if ctx.risk_score >= THRESHOLDS[AlertType.AVOID_AREA]:
        alerts.append(AlertType.AVOID_AREA)
    elif ctx.risk_score >= THRESHOLDS[AlertType.HIGH_RISK_AREA]:
        alerts.append(AlertType.HIGH_RISK_AREA)
    return alerts


def render_template(alert_type: AlertType, ctx: AlertContext) -> str:
    templates = {
        AlertType.HIGH_RISK_AREA: (
            "[MosquiSense-LMC] Ward {ward_name} risk {risk_score}/100. "
            "15-day outbreak probability {prob:.0%}. Remove stagnant water."
        ),
        AlertType.AVOID_AREA: (
            "[MosquiSense-LMC] CRITICAL: Avoid {ward_name} area. "
            "Risk {risk_score}/100. Follow health advisories."
        ),
    }
    tpl = templates.get(alert_type, "[MosquiSense] Alert for {ward_name}")
    return tpl.format(
        ward_name=ctx.ward_name,
        risk_score=ctx.risk_score,
        prob=ctx.outbreak_probability_15d,
    )
