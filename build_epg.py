#!/usr/bin/env python3
"""
IPTV Curated EPG Generator
Fetches upstream compressed XMLTV guides, extracts matching channel schedules,
and generates a lightweight epg.xml.gz tailored specifically for iptv-curated.
"""

import gzip
import re
import sys
import urllib.request

EPG_OUTPUT = "epg.xml.gz"

# Source XML.gz feeds mapped to target channel IDs
EPG_SOURCES = {
    "https://epgshare01.online/epgshare01/epg_ripper_TR1.xml.gz": {
        "TRT.1.HD.tr",
        "TRT.SPOR.HD.tr",
        "TRT.WORLD.HD.tr",
        "TRT.BELGESEL.HD.tr",
        "TRT.ÇOCUK.HD.tr",
        "TV8.HD.tr",
        "KANAL.D.HD.tr",
        "FOX.HD.tr",
        "STAR.TV.HD.tr",
        "NTV.HD.tr",
    },
    "https://epgshare01.online/epgshare01/epg_ripper_US2.xml.gz": {
        "HBO.Zone.HD.us2",
        "Cinemax.HD.us2",
        "Cinemax.Classics.us2",
        "Starz.Cinema.HD.us2",
        "Starz.Comedy.HD.us2",
        "Paramount.Network.HD.us2",
        "Syfy.HD.us2",
        "IFC.HD.us2",
        "AMC.HD.us2",
        "Cartoon.Network.HD.us2",
        "Boomerang.us2",
        "Disney.XD.HD.us2",
        "Science.Channel.HD.us2",
        "National.Geographic.HD.us2",
        "National.Geographic.Wild.HD.us2",
        "Animal.Planet.HD.us2",
        "BBC.America.HD.us2",
        "NBA.TV.HD.us2",
    },
    "https://epgshare01.online/epgshare01/epg_ripper_UK1.xml.gz": {
        "SkySp.F1.uk",
        "Sky.News.HD.uk",
    },
    "https://epgshare01.online/epgshare01/epg_ripper_SG1.xml.gz": {
        "Deutsche.Welle.(English).sg",
        "NHK.World.–.Japan.(HD).sg",
        "Bloomberg.Television.(HD).sg",
        "CNA.(HD).sg",
    },
    "https://epgshare01.online/epgshare01/epg_ripper_FR1.xml.gz": {
        "France.24.Anglais.fr",
    },
    "https://epgshare01.online/epgshare01/epg_ripper_ALJAZEERA1.xml.gz": {
        "AlJazeera.English.net",
    },
    "https://epgshare01.online/epgshare01/epg_ripper_AU1.xml.gz": {
        "Moviesphere.au",
    },
}


# Custom display-name aliases for robust player matching across various IPTV apps
CHANNEL_ALIASES = {
    "Moviesphere.au": ["MovieSphere", "Moviesphere", "MovieSphere UK"],
    "FOX.HD.tr": ["NOW TV", "NOW"],
    "SkySp.F1.uk": ["Sky Sports F1"],
    "Deutsche.Welle.(English).sg": ["DW English"],
    "Bloomberg.Television.(HD).sg": ["Bloomberg Originals"],
    "National.Geographic.HD.us2": ["Nat Geo"],
}


def fetch_and_extract(url: str, target_ids: set[str]) -> tuple[list[str], list[str]]:
    print(f"Fetching EPG source: {url.split('/')[-1]}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = gzip.decompress(resp.read()).decode("utf-8", errors="ignore").replace("\r\n", "\n")
    except Exception as err:
        print(f"  [-] Failed to fetch {url}: {err}", file=sys.stderr)
        return [], []

    channels = []
    programmes = []

    for m in re.finditer(r"(<channel id=\"([^\"]+)\">.*?</channel>)", data, re.DOTALL):
        ch_id = m.group(2)
        if ch_id in target_ids:
            ch_xml = m.group(1)
            if ch_id in CHANNEL_ALIASES:
                aliases_to_add = [
                    f'    <display-name lang="en">{alias}</display-name>'
                    for alias in CHANNEL_ALIASES[ch_id]
                    if f">{alias}<" not in ch_xml
                ]
                if aliases_to_add:
                    pos = ch_xml.find(">") + 1
                    ch_xml = ch_xml[:pos] + "\n" + "\n".join(aliases_to_add) + ch_xml[pos:]
            channels.append(ch_xml)

    for m in re.finditer(r"(<programme [^>]*channel=\"([^\"]+)\".*?</programme>)", data, re.DOTALL):
        if m.group(2) in target_ids:
            programmes.append(m.group(1))

    print(f"  [+] Extracted {len(channels)} channels and {len(programmes)} programmes")
    return channels, programmes


def main():
    all_channels = []
    all_programmes = []

    for url, ids in EPG_SOURCES.items():
        chs, progs = fetch_and_extract(url, ids)
        all_channels.extend(chs)
        all_programmes.extend(progs)

    if not all_channels:
        print("Error: No EPG channels could be parsed.", file=sys.stderr)
        sys.exit(1)

    xml_header = '<?xml version="1.0" encoding="UTF-8"?>\n<tv generator-info-name="iptv-curated">\n'
    xml_body = "\n".join(all_channels) + "\n" + "\n".join(all_programmes) + "\n"
    xml_footer = "</tv>\n"

    full_xml = xml_header + xml_body + xml_footer
    compressed = gzip.compress(full_xml.encode("utf-8"))

    with open(EPG_OUTPUT, "wb") as f:
        f.write(compressed)

    print(
        f"\nSuccessfully generated {EPG_OUTPUT}:"
        f" {len(all_channels)} channels, {len(all_programmes)} programmes"
        f" ({len(compressed) // 1024} KB compressed)"
    )


if __name__ == "__main__":
    main()
