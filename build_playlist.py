#!/usr/bin/env python3
"""
IPTV Curated Playlist Generator
Fetches sources from iptv-org, filters desired channels, strips all group metadata (flat list),
and outputs a clean, auto-updating playlist.m3u in the exact preferred order.
"""

import re
import sys
import urllib.request

SOURCES = [
    "https://iptv-org.github.io/iptv/index.m3u",
    "https://iptv-org.github.io/iptv/countries/tr.m3u",
]

OUTPUT_FILE = "playlist.m3u"

# Target channels in exact order of appearance
TARGET_CHANNELS = [
    # --- Global / English (Culture, Movies & Documentaries) ---
    {
        "id": "dw_english",
        "name": "DW English (1080p)",
        "pattern": r"DW English \(1080p\)",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/75/Deutsche_Welle_symbol_2012.svg/960px-Deutsche_Welle_symbol_2012.svg.png",
    },
    {
        "id": "nhk_world",
        "name": "NHK World-Japan (1080p)",
        "pattern": r"NHK World-Japan \(1080p\)",
        "logo": "https://jiotvimages.cdn.jio.com/dare_images/images/NHK_World_Japan.png",
    },
    {
        "id": "moviesphere",
        "name": "MovieSphere (1080p)",
        "pattern": r"MovieSphere UK \(1080p\)",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d4/Lionsgate_2019.svg/960px-Lionsgate_2019.svg.png",
    },
    {
        "id": "trt_world",
        "name": "TRT World (1440p)",
        "direct_url": "https://tv-trtworld.medya.trt.com.tr/master.m3u8",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/27/TRT_World.svg/960px-TRT_World.svg.png",
    },
    {
        "id": "bloomberg_originals",
        "name": "Bloomberg Originals (1080p)",
        "pattern": r"Bloomberg Originals \(1080p\)",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/56/Bloomberg_Logo.svg/960px-Bloomberg_Logo.svg.png",
    },
    {
        "id": "france24_en",
        "name": "France 24 English (1080p)",
        "pattern": r"France 24 English \(1080p\)",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/France_24_logo.svg/960px-France_24_logo.svg.png",
    },
    {
        "id": "sky_news",
        "name": "Sky News (1080p)",
        "pattern": r"Sky News.*1080p|Sky News$",
        "logo": "https://upload.wikimedia.org/wikipedia/en/thumb/a/a8/Sky_News_logo_2020.svg/960px-Sky_News_logo_2020.svg.png",
    },
    {
        "id": "aljazeera_en",
        "name": "Al Jazeera English (1080p)",
        "pattern": r"Al Jazeera English \(1080p\)",
        "logo": "https://upload.wikimedia.org/wikipedia/en/thumb/f/f2/Al_Jazeera_English_logo.svg/960px-Al_Jazeera_English_logo.svg.png",
    },
    {
        "id": "cna",
        "name": "CNA (1080p)",
        "pattern": r"CNA \(Singapore\) \(1080p\)",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/63/CNA_%28TV_network%29_logo.svg/960px-CNA_%28TV_network%29_logo.svg.png",
    },

    # --- National / Turkish (Occasional Games, Mainstream & Documentary) ---
    {
        "id": "trt_1",
        "name": "TRT 1 (1440p)",
        "pattern": r"TRT 1 \(1440p\)",
        "direct_url": "https://tv-trt1.medya.trt.com.tr/master.m3u8",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/85/TRT_1_logo_%282021-%29.svg/960px-TRT_1_logo_%282021-%29.svg.png",
    },
    {
        "id": "trt_spor",
        "name": "TRT Spor (1440p)",
        "direct_url": "https://tv-trtspor1.medya.trt.com.tr/master.m3u8",
        "logo": "https://i.imgur.com/6tv0zxh.png",
    },
    {
        "id": "tv8",
        "name": "TV8 (1080p)",
        "pattern": r"TV8 \(Turkiye\) \(1080p\)",
        "logo": "https://upload.wikimedia.org/wikipedia/tr/thumb/6/68/Tv8_Yeni_Logo.png/960px-Tv8_Yeni_Logo.png",
    },
    {
        "id": "kanal_d",
        "name": "Kanal D (1080p)",
        "pattern": r"Kanal D \(Turkiye\) \(1080p\)",
        "logo": "https://i.imgur.com/9o1atM6.png",
    },
    {
        "id": "now_tv",
        "name": "NOW TV (720p)",
        "pattern": r"NOW TV \(720p\)",
        "logo": "https://i.imgur.com/5EYjWK7.png",
    },
    {
        "id": "star_tv",
        "name": "Star TV (720p)",
        "pattern": r"Star TV \(Turkiye\) \(720p\)",
        "logo": "https://i.imgur.com/9O3DHRB.png",
    },
    {
        "id": "ntv",
        "name": "NTV (720p)",
        "pattern": r"NTV \(Turkiye\)",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/NTV_%28Turkey%29_logo.svg/960px-NTV_%28Turkey%29_logo.svg.png",
    },
    {
        "id": "trt_belgesel",
        "name": "TRT Belgesel (1440p)",
        "direct_url": "https://tv-trtbelgesel.medya.trt.com.tr/master.m3u8",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b3/TRT_Belgesel_logo.svg/960px-TRT_Belgesel_logo.svg.png",
    },
]


def fetch_source(url: str) -> str:
    print(f"Fetching: {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def parse_iptv_org(raw_text: str) -> dict[str, tuple[str, str]]:
    """
    Parses raw M3U text and indexes entries by matched channel name.
    """
    parsed = {}
    chunks = raw_text.split("#EXTINF:")
    for chunk in chunks[1:]:
        lines = [l.strip() for l in chunk.strip().split("\n") if l.strip()]
        if len(lines) < 2:
            continue
        header = lines[0]
        url = lines[-1]
        name = header.split(",")[-1].strip()
        parsed[name] = (header, url)
    return parsed


def main():
    combined_raw = ""
    for src in SOURCES:
        try:
            combined_raw += fetch_source(src) + "\n"
        except Exception as err:
            print(f"Warning: Failed to fetch {src}: {err}", file=sys.stderr)

    available_streams = parse_iptv_org(combined_raw)
    ordered_entries = []

    for item in TARGET_CHANNELS:
        display_name = item["name"]
        logo_url = item.get("logo", "")
        stream_url = item.get("direct_url")

        # If not direct URL, search in parsed sources via pattern
        if not stream_url and "pattern" in item:
            pat = re.compile(item["pattern"], re.IGNORECASE)
            for channel_title, (header, url) in available_streams.items():
                if pat.search(channel_title):
                    stream_url = url
                    break

        if not stream_url:
            print(f"  [-] Failed to resolve stream for: {display_name}", file=sys.stderr)
            continue

        # Build clean #EXTINF line without any group-title
        extinf_line = f'#EXTINF:-1 tvg-logo="{logo_url}",{display_name}'
        ordered_entries.append(f"{extinf_line}\n{stream_url}")
        print(f"  [+] Added: {display_name}")

    if not ordered_entries:
        print("Error: No channels could be matched or resolved.", file=sys.stderr)
        sys.exit(1)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n\n")
        f.write("\n\n".join(ordered_entries) + "\n")

    print(f"\nSuccessfully created {OUTPUT_FILE} with {len(ordered_entries)} channels in ordered sequence.")


if __name__ == "__main__":
    main()
