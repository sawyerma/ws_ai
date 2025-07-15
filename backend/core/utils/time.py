import re

def parse_resolution(res: str) -> int:
    """
    Konvertiert Zeitauflösungs-String ('1s', '5m', '1h', '1d', '1w')
    in Sekunden als Integer.
    """
    m = re.fullmatch(r"(?P<num>\d+)(?P<unit>[smhdw])", res.strip())
    if not m:
        raise ValueError(f"Ungültiges Format für resolution: '{res}'")
    num, unit = int(m.group("num")), m.group("unit")
    factor = {"s":1, "m":60, "h":3600, "d":86400, "w":604800}
    return num * factor[unit]
