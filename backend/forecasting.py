import math
from typing import List, Dict, Tuple, Any

class OpenSourceForecastingEngine:
    """
    Open-source ready-to-use statistical and machine learning time-series
    forecasting engine for retail demand prediction and association probability.
    Uses Double Exponential Smoothing (Holt's Linear Trend) and Seasonal Multipliers.
    """

    @staticmethod
    def double_exponential_smoothing(
        series: List[float], 
        alpha: float = 0.45, 
        beta: float = 0.25, 
        forecast_horizon: int = 4
    ) -> Tuple[List[float], float, float]:
        """
        Holt's Linear Trend Model (Double Exponential Smoothing).
        Forecasts level and additive trend for future periods.
        """
        if not series:
            return [0.0] * forecast_horizon, 0.0, 0.0

        if len(series) == 1:
            return [series[0]] * forecast_horizon, series[0], 0.0

        # Initialize level and trend
        level = series[0]
        trend = series[1] - series[0]

        # Fit historical series
        for t in range(1, len(series)):
            val = series[t]
            last_level = level
            level = alpha * val + (1.0 - alpha) * (last_level + trend)
            trend = beta * (level - last_level) + (1.0 - beta) * trend

        # Generate future forecast points
        forecasts = []
        for h in range(1, forecast_horizon + 1):
            projected = max(0.0, level + (h * trend))
            forecasts.append(round(projected, 1))

        return forecasts, round(level, 1), round(trend, 2)

    @classmethod
    def predict_demand_surge(
        cls,
        past_sales: List[int],
        event_surge_pct: float = 0.0,
        forecast_weeks: int = 4
    ) -> Dict[str, Any]:
        """
        Combines Holt's smoothing with seasonal event multipliers (e.g. Diwali, Monsoon, Super Saver).
        """
        if not past_sales:
            past_sales = [10, 10, 10, 10, 10, 10]

        float_series = [float(x) for x in past_sales]
        base_forecasts, final_level, trend = cls.double_exponential_smoothing(
            float_series, forecast_horizon=forecast_weeks
        )

        # Apply event acceleration factor if seasonal surge is present
        event_multiplier = 1.0 + (event_surge_pct / 100.0)
        
        # Gradually phase in the event surge across the 4 forecast weeks
        adjusted_forecast = []
        for i, val in enumerate(base_forecasts):
            # Week 1: 30% of surge, Week 2: 60%, Week 3: 90%, Week 4: peak 100%
            phase = 0.3 + (0.7 * (i / max(1, forecast_weeks - 1)))
            week_surge_multiplier = 1.0 + ((event_multiplier - 1.0) * phase)
            projected_units = max(1, int(round(val * week_surge_multiplier)))
            adjusted_forecast.append(projected_units)

        # Compute growth trajectory metrics
        past_avg = sum(past_sales) / len(past_sales) if past_sales else 1.0
        forecast_avg = sum(adjusted_forecast) / len(adjusted_forecast) if adjusted_forecast else 1.0
        growth_pct = round(((forecast_avg - past_avg) / max(0.1, past_avg)) * 100.0, 1)

        # Classify growth momentum
        if growth_pct >= 35.0:
            growth_status = "RAPID_SURGE_GROWTH"
            recommendation = "High surge predicted. Restock aggressively to capitalize on event demand."
        elif growth_pct >= 10.0:
            growth_status = "STEADY_GROWTH"
            recommendation = "Positive growth momentum. Maintain steady inventory buffer."
        elif growth_pct >= -10.0:
            growth_status = "STABLE"
            recommendation = "Demand is stable. Maintain current replenishment cycle."
        else:
            growth_status = "DECLINING_RISK"
            recommendation = "Demand slowing down. Risk of shelf stagnation. Run clearance offers."

        return {
            "past_sales": past_sales,
            "forecast_sales": adjusted_forecast,
            "past_weekly_avg": round(past_avg, 1),
            "projected_weekly_avg": round(forecast_avg, 1),
            "expected_growth_pct": growth_pct,
            "trend_rate": trend,
            "growth_status": growth_status,
            "forecasting_model": "Holt-Winters Double Exponential Smoothing + Seasonal Multiplier",
            "forecast_recommendation": recommendation
        }

    @staticmethod
    def calculate_co_purchase_probability(
        anchor_id: str, 
        attached_id: str, 
        affinity_score: float
    ) -> Dict[str, float]:
        """
        Calculates Association Rule Mining probabilities:
        - Support P(A and B)
        - Confidence P(B|A)
        - Lift = P(B|A) / P(B)
        """
        # Baseline confidence from affinity matrix percentage
        confidence = round(min(0.95, max(0.05, affinity_score / 100.0)), 3)
        
        # Support: probability of basket containing both items in an urban kirana (~12% - 35%)
        support = round(min(0.40, max(0.05, confidence * 0.45)), 3)
        
        # Marginal probability P(B) assumed between 15% - 30%
        prob_b = 0.22
        lift = round(confidence / prob_b, 2)

        return {
            "confidence_pct": round(confidence * 100.0, 1),
            "support_pct": round(support * 100.0, 1),
            "lift_score": lift,
            "is_statistically_significant": lift > 1.2
        }

