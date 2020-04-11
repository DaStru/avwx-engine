"""
Builds the master station list

Source file for airports.csv and runways.csv can be downloaded from
http://ourairports.com/data/

Source file for stations.txt can be downloaded from
https://www.aviationweather.gov/docs/metar/stations.txt
"""

# stdlib
import csv
import json
from pathlib import Path

# module
from find_bad_stations import BAD_PATH, GOOD_PATH, load_stations

_DATA = Path("data")
AIRPORT_PATH = _DATA / "airports.csv"
STATION_PATH = _DATA / "stations.txt"
RUNWAY_PATH = _DATA / "runways.csv"
OUTPUT_PATH = Path("..", "avwx", "data", "stations.json")

ACCEPTED_STATION_TYPES = [
    "balloonport",
    "closed",
    "heliport",
    "large_airport",
    "medium_airport",
    "seaplane_base",
    "small_airport",
]


FILE_REPLACE = {
    "Æ\x8f": "Ə",
    "Ã\x81": "Á",
    "Ã„": "Ä",
    "Ã…": "Å",
    "Ã‚": "Â",
    "Ãƒ": "Ã",
    "Ã¡": "á",
    "áº£": "ả",
    "áº¥": "ấ",
    "Ã£": "ã",
    "Ã¢": "â",
    "Äƒ": "ă",
    "Ã¤": "ä",
    "Ã¥": "å",
    "áº©": "ẩ",
    "Ä…": "ą",
    "Ä\x81": "ā",
    "áºµ": "ẵ",
    "Ã¦": "æ",
    "ÃŸ": "ß",
    "ÄŒ": "Č",
    "Ã‡": "Ç",
    "Ä†": "Č",
    "Ã§": "ç",
    "Ä‡": "ć",
    "Ä\x8d": "č",
    "ÄŽ": "Ď",
    "Ä\x90": "Đ",
    "Ä\x8f": "ď",
    "Ä‘": "đ",
    "Ã‰": "É",
    "Ã©": "é",
    "È©": "ę",
    "Ä™": "ę",
    "Ã¨": "è",
    "Ã«": "ë",
    "Ä“": "ē",
    "Ä—": "ė",
    "Ãª": "ê",
    "Ä›": "ě",
    "É™": "ə",
    "áº¿": "ế",
    "ÄŸ": "ğ",
    "Ä¡": "ġ",
    "Ä£": "ģ",
    "Ä°": "İ",
    "ÃŽ": "Î",
    "Ã\x8d": "Í",
    "Ã¯": "ï",
    "Ã¬": "ì",
    "Ã­č": "í",
    "Ä±": "ı",
    "Ã®": "î",
    "Ä«": "ī",
    "Ä¯": "į",
    "Ã\xad": "í",
    "Ä·": "ķ",
    "Å\x81": "Ł",
    "Å‚": "ł",
    "Ä¾": "ľ",
    "Ã‘": "Ñ",
    "Ã±": "ñ",
    "Å„": "ń",
    "Åˆ": "ň",
    "Ä¼": "ņ",
    "Å†": "ņ",
    "Ã–": "Ö",
    "ÅŒ": "Ō",
    "Ã”": "Ô",
    "Ã“": "Ó",
    "Ã˜": "Ø",
    "Å\x90": "Ő",
    "Ãµ": "õ",
    "Ã°": "ð",
    "Ã²": "ò",
    "Ã¶": "ö",
    "Ã³": "ó",
    "á»“": "ồ",
    "á»‘": "ố",
    "á»™": "ộ",
    "Ã´": "ố",
    "Æ¡": "ơ",
    "Å‘": "ő",
    "Ã¸": "ø",
    "Å\x8d": "ō",
    "Å\x8f": "ŏ",
    "Ãž": "Þ",
    "Å˜": "Ř",
    "Å™": "ř",
    "Å ": "Š",
    "Åš": "Ś",
    "Åž": "Ş",
    "Å›": "ś",
    "Å¡": "š",
    "È™": "ș",
    "ÅŸ": "ș",
    "Å\x9d": "ŝ",
    "È›": "ț",
    "Å¥": "ť",
    "Å£": "ț",
    "Ãœ": "Ü",
    "Ãš": "Ú",
    "Ã¼": "ü",
    "Ãº": "ú",
    "Å«": "ū",
    "Å¯": "ů",
    "Ã»": "û",
    "Å³": "ų",
    "á»±": "ự",
    "Ã½": "ý",
    "Å½": "Ž",
    "Å»": "Ż",
    "Åº": "ź",
    "Å¼": "ż",
    "Å¾": "ž",
    "Â¡": "¡",
    "â€“": "–",
    "â€™": "'",
    "â€ž": "„",
    "â€œ": "“",
    "â€\x9d": "”",
    # Key for another replacement
    "Ã†": "Æ",
    # In-place character
    "Â°": "°",
    "Âº": "º",
    # Last because too broad
    "Ã ": "à",
}


def nullify(data: dict) -> dict:
    """
    Nullify empty strings in a dict
    """
    for key, val in data.items():
        if val == "":
            data[key] = None
    return data


def format_coord(coord: str) -> float:
    """
    Convert coord string to float
    """
    neg = -1 if coord[-1] in ("S", "W") else 1
    return neg * float(coord[:-1].strip().replace(" ", "."))


def clean_source_file():
    """
    Cleans the source data files before parsing
    """
    with AIRPORT_PATH.open("r") as fin:
        text = fin.read()
    for find, replace in FILE_REPLACE.items():
        text = text.replace(find, replace)
    with AIRPORT_PATH.open("w") as fout:
        fout.write(text)


def format_station(station: [str]) -> dict:
    """
    Converts source station list into info dict
    """
    try:
        elev_ft = float(station[6])
        elev_m = round(elev_ft * 0.3048)
        elev_ft = round(elev_ft)
    except ValueError:
        elev_ft, elev_m = None, None
    iloc = station[9].find("-")
    ret = {
        "type": station[2],
        "name": station[3],
        "reporting": None,
        "latitude": float(station[4]),
        "longitude": float(station[5]),
        "elevation_ft": elev_ft,
        "elevation_m": elev_m,
        "country": station[9][:iloc],
        "state": station[9][iloc + 1 :],
        "city": station[10],
        "icao": station[12].upper(),
        "iata": station[13].upper(),
        "website": station[15],
        "wiki": station[16],
        "note": station[17],
    }
    return nullify(ret)


def build_stations() -> dict:
    """
    Builds the station dict from source file
    """
    stations = {}
    data = csv.reader(AIRPORT_PATH.open())
    next(data)  # Skip header
    for station in data:
        icao = station[12].upper()
        if len(icao) != 4:
            continue
        if station[2] in ACCEPTED_STATION_TYPES:
            stations[icao] = format_station(station)
    return stations


def add_missing_stations(stations: dict) -> dict:
    """
    Add non-airport stations from NOAA
    """
    for line in STATION_PATH.open().readlines():
        # Must be data line with METAR reporting
        if len(line) != 84 or line[0] == "!" or line[62] != "X":
            continue
        icao = line[20:24].strip().upper()
        if not icao or icao in stations:  # or icao in BAD_STATIONS:
            continue
        elev_m = int(line[55:59].strip())
        ret = {
            "type": "weather_station",
            "name": line[3:19].strip(),
            "reporting": None,
            "latitude": format_coord(line[39:45]),
            "longitude": format_coord(line[47:54]),
            "elevation_ft": round(elev_m * 3.28084),
            "elevation_m": elev_m,
            "country": line[81:83].strip(),
            "state": line[:2],
            "city": None,
            "icao": icao,
            "iata": line[26:29].strip().upper(),
            "website": None,
            "wiki": None,
            "note": None,
        }
        stations[icao] = nullify(ret)
    return stations


def add_runways(stations: dict) -> dict:
    """
    Add runway information to station if availabale
    """
    data = csv.reader(RUNWAY_PATH.open())
    next(data)  # Skip header
    for runway in data:
        data = {
            "length_ft": int(runway[3]) if runway[3] else 0,
            "width_ft": int(runway[4]) if runway[4] else 0,
            "ident1": runway[8],
            "ident2": runway[14],
        }
        icao = runway[2]
        if icao in stations:
            if "runways" in stations[icao]:
                stations[icao]["runways"].append(data)
            else:
                stations[icao]["runways"] = [data]
    # Sort runways by longest length and add missing nulls
    for icao in stations:
        if "runways" in stations[icao]:
            stations[icao]["runways"].sort(key=lambda x: x["length_ft"], reverse=True)
        else:
            stations[icao]["runways"] = None
    return stations


def add_reporting(stations: dict) -> dict:
    """
    Add reporting boolean to station if available
    """
    good = load_stations(GOOD_PATH)
    bad = load_stations(BAD_PATH)
    for icao in stations:
        if icao in good:
            stations[icao]["reporting"] = True
        elif icao in bad:
            stations[icao]["reporting"] = False
        # else unknown
    return stations


def main() -> int:
    """
    Build/update the stations.json master file
    """
    clean_source_file()
    stations = build_stations()
    stations = add_missing_stations(stations)
    stations = add_reporting(stations)
    stations = add_runways(stations)
    json.dump(
        stations, OUTPUT_PATH.open("w"), sort_keys=True, indent=2, ensure_ascii=False
    )
    return 0


if __name__ == "__main__":
    main()
