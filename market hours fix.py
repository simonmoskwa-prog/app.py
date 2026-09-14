"""
FIX: Börsenzeiten-Erkennung (is_open) im Stage-Analysis Dashboard.

PROBLEM IM ORIGINAL:
    now_local = datetime.datetime.now()
    current_minute_of_day = now_local.hour * 60 + now_local.minute

datetime.datetime.now() liefert die SYSTEMZEIT DES SERVERS.
Auf Streamlit Community Cloud läuft der Server in UTC, nicht in
deutscher Zeit. Der Code rechnet aber mit fest einprogrammierten
Minutenfenstern (z.B. 930-1320 für die US-Börse), die für deutsche
Ortszeit (CET/CEST) gedacht waren. Dadurch wird UTC gegen ein
CET/CEST-Fenster geprüft -> Versatz von 1-2 Stunden. Zusätzlich
verschiebt sich die US-Sommerzeit nicht synchron zur deutschen
Sommerzeit (paar Wochen im Frühjahr/Herbst), was einen weiteren
Fehler verursacht. Ergebnis: is_open ist praktisch fast immer False.

LÖSUNG:
Echte Zeitzonen (zoneinfo) verwenden und für jede Börse in ihrer
EIGENEN lokalen Zeit prüfen, ob gerade Handelszeit ist - statt alles
über eine angenommene deutsche Ortszeit umzurechnen.
"""

import datetime
from zoneinfo import ZoneInfo


def is_market_open(ticker: str) -> bool:
    """
    Prüft anhand des Tickers, ob die zugehörige Börse gerade
    (in ihrer eigenen lokalen Zeit) geöffnet hat.
    """
    now_utc = datetime.datetime.now(datetime.timezone.utc)

    eu_identifiers = ["GDAXI", "STOXX", "DE", "STX", "WA", "PA", "F"]
    is_european = any(identifier in ticker for identifier in eu_identifiers)

    if is_european:
        # Xetra / Euronext etc. laufen nach Europe/Berlin-Zeit
        tz = ZoneInfo("Europe/Berlin")
        open_time = datetime.time(9, 0)
        close_time = datetime.time(17, 30)
    else:
        # NYSE / Nasdaq laufen nach US-Ostküstenzeit (regelt DST automatisch)
        tz = ZoneInfo("America/New_York")
        open_time = datetime.time(9, 30)
        close_time = datetime.time(16, 0)

    now_local = now_utc.astimezone(tz)
    is_weekday = now_local.weekday() < 5  # Mo=0 ... Fr=4

    return is_weekday and open_time <= now_local.time() <= close_time


# ---------------------------------------------------------
# So wird es in get_data_with_info() eingebaut:
# ---------------------------------------------------------
#
# Ersetze im Original-Code den kompletten try-Block, der is_open
# berechnet, durch einfach:
#
#     try:
#         info = yticker.info
#         currency = info.get("currency", "USD")
#         exchange = info.get("exchange", "N/A")
#         company_name = info.get("longName") or info.get("shortName") or ticker
#         is_open = is_market_open(ticker)
#     except Exception:
#         is_open = False
#
# und importiere oben im Skript zusätzlich:
#     from zoneinfo import ZoneInfo
