"""
Data processing utilities for pharmacy site selection analysis.
"""
import json
import math
from typing import List, Dict, Any, Tuple, Optional

def to_num(x: Any) -> float:
    """Convert value to float, handling N/A and empty values."""
    try:
        if isinstance(x, str) and x.strip().upper() in ("N/A", "NA", ""):
            return float('nan')
        return float(x)
    except Exception:
        return float('nan')


def pick_display_name(record: Dict) -> Optional[str]:
    """Extract display name from record, trying multiple possible keys."""
    for k in ('place name', 'place_name', 'place', 'name'):
        v = record.get(k)
        if v:
            return str(v)
    return None


def process_sites(
    scores: Dict,
    criterion_weights: Dict[str, float]
) -> Tuple[List[Dict], List[str]]:
    """
    Process raw scores data into structured site information.

    Args:
        scores: Dictionary containing the scores data.
        criterion_weights: Dict mapping criteria names to their weights.

    Returns:
        Tuple of (processed_sites, warnings)
    """
    warnings: List[str] = []
    sites: List[Dict] = []

    for key, rec in scores.items():
        site = _process_single_site(key, rec, warnings, criterion_weights)
        sites.append(site)

    if not sites:
        warnings.append('No sites parsed from scores data.')

    return sites, warnings
def _process_single_site(
    key: str,
    rec: Dict,
    warnings: List[str],
    criterion_weights: Dict[str, float]
) -> Dict:
    """Process a single site record."""
    place = pick_display_name(rec)
    lat = rec.get('lat')
    lng = rec.get('lng')
    price = rec.get('price', 0)

    site = {
        'id': key,
        'display_name': place or key,
        'raw_place': place,
        'lat': None,
        'lng': None,
        'price': price,
        'scores': {},
        'details': {},
        'competing_pharmacies': 0,
        'nearby Businesses within 500 meters': rec.get("data", {}).get("nearby Businesses within 500 meters", 0),
        "average speed in km": rec.get("data", {}).get("Average Vehicle Speed in km"),
        "Age above 35": rec.get("data", {}).get("percentage_age_above_35"),
        "Average Income": rec.get("data", {}).get("avg_income"),
        "pharmacies_per_10k_population": rec.get("data", {}).get("pharmacies_per_10k_population")
    }

    try:
        site['lat'] = float(lat) if lat is not None else None
    except Exception:
        site['lat'] = None

    try:
        site['lng'] = float(lng) if lng is not None else None
    except Exception:
        site['lng'] = None

    total = 0.0
    scores = rec.get('scores', {}) or {}

    for crit, weight in criterion_weights.items():
        crit_obj = scores.get(crit, {}) or {}
        raw_overall = to_num(crit_obj.get('overall_score', float('nan')))

        if not math.isnan(raw_overall):
            if raw_overall < 0:
                warnings.append(f"{key}: {crit} overall_score negative ({raw_overall})")
            if raw_overall > weight + 1e-6:
                warnings.append(f"{key}: {crit} overall_score ({raw_overall}) exceeds criterion weight ({weight})")

        site['scores'][f'{crit}_raw_overall'] = raw_overall
        site['scores'][f'{crit}_score'] = raw_overall if not math.isnan(raw_overall) else 0.0
        if not math.isnan(raw_overall):
            total += raw_overall

        # process details
        crit_details = crit_obj.get('details') or {}
        details = {}
        for dk, dv in crit_details.items():
            val = to_num(dv)
            safe_key = dk.strip()
            details[f'{crit}__{safe_key}'] = val
            details[f'{crit}__{safe_key}_weighted'] = (val / 100.0) * weight if not math.isnan(val) else float('nan')
        if not details:
            details[f'{crit}__MISSING'] = float('nan')
            details[f'{crit}__MISSING_weighted'] = float('nan')

        site['details'].update(details)

        if crit in ('competitive', 'competition'):
            site['competing_pharmacies'] = crit_details["competeing pharmacies around"]

    site['total_score'] = total
    max_total = sum(criterion_weights.values())
    site['total_pct'] = (total / max_total) * 100.0 if max_total > 0 else float('nan')

    if site['lat'] is None or site['lng'] is None:
        if not site['raw_place']:
            warnings.append(f"{key}: missing lat/lng and no place name provided")

    return site

def calculate_statistics(sites: List[Dict]) -> Dict[str, float]:
    """Calculate aggregate statistics for all sites."""
    if not sites:
        return {
            'average_score': 0.0,
            'average_price': 0.0,
            'total_competing_pharmacies': 0,
            'sites_with_coordinates': 0,
            'total_sites': 0
        }
    
    valid_scores = [s['total_score'] for s in sites if not math.isnan(s['total_score'])]
    valid_prices = [s['price'] for s in sites if s['price'] and s['price'] > 0]
    
    return {
        'average_score': sum(valid_scores) / len(valid_scores) if valid_scores else 0.0,
        'average_price': sum(valid_prices) / len(valid_prices) if valid_prices else 0.0,
        'total_competing_pharmacies': sum(s.get('competing_pharmacies', 0) for s in sites),
        'sites_with_coordinates': len([s for s in sites if s['lat'] and s['lng']]),
        'total_sites': len(sites)
    }