import numpy as np

def grade_crop(fertilizer, organic, soil, irrigation, quantity, quality):
    # Advanced scoring logic: weighted categorical encoding and feature interactions
    fertilizer_weights = {
        'urea': 0.05,
        'compost': 0.18,
        'vermicompost': 0.20,
        'biofertilizer': 0.22,
        'npk': 0.10,
        'dap': 0.08
    }
    organic_weight = 0.25 if organic.lower() == 'organic' else 0.10
    soil_weights = {
        'loamy': 0.18,
        'sandy': 0.08,
        'sandy loam': 0.15,
        'clay': 0.10,
        'silt': 0.12
    }
    irrigation_weights = {
        'drip': 0.15,
        'sprinkler': 0.12,
        'flood': 0.05,
        'manual': 0.03
    }
    quality_weights = {
        'premium': 0.18,
        'high': 0.14,
        'medium': 0.08,
        'low': 0.03
    }
    # Feature interaction: organic + compost/vermicompost/biofertilizer
    interaction_bonus = 0.08 if organic.lower() == 'organic' and fertilizer.lower() in ['compost', 'vermicompost', 'biofertilizer'] else 0

    score = 0.0
    score += fertilizer_weights.get(fertilizer.lower(), 0.05)
    score += organic_weight
    score += soil_weights.get(soil.lower(), 0.08)
    score += irrigation_weights.get(irrigation.lower(), 0.03)
    score += quality_weights.get(quality.lower(), 0.03)
    score += min(0.12, max(0, float(quantity)/500))  # up to 0.12 for large quantity
    score += interaction_bonus

    # Clamp score between 0 and 1
    score = min(1.0, max(0.0, score))

    # Grade logic (more granular)
    if score >= 0.85:
        grade = 'A+'
        cert = 'Organic Premium Plus'
    elif score >= 0.7:
        grade = 'A'
        cert = 'Organic Premium'
    elif score >= 0.55:
        grade = 'B'
        cert = 'Certified Good'
    elif score >= 0.4:
        grade = 'C'
        cert = 'Standard'
    else:
        grade = 'D'
        cert = 'Needs Improvement'
    return round(score, 2), grade, cert