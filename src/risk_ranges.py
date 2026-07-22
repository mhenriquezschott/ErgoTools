RISK_BANDS = (
    (0.0, 25.0, "Low Risk", "#19B83F", "0 - 25%"),
    (25.0, 37.5, "Moderate Risk", "#F5C400", "> 25% - 37.5%"),
    (37.5, 50.0, "Moderate High Risk", "#FF8A19", "> 37.5% - 50%"),
    (50.0, 100.0, "High Risk", "#FF3B30", "> 50%"),
)


def risk_band(probability):
    value = max(0.0, min(100.0, float(probability)))
    if value <= 25.0:
        return RISK_BANDS[0]
    if value <= 37.5:
        return RISK_BANDS[1]
    if value <= 50.0:
        return RISK_BANDS[2]
    return RISK_BANDS[3]
