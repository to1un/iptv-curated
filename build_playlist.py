#!/usr/bin/env python3
"""
IPTV Curated Playlist Generator
Fetches sources from iptv-org and doms9, filters desired channels, maps EPG ids,
and outputs a clean, auto-updating playlist.m3u in the exact preferred order.
"""

import re
import sys
import urllib.request

SOURCES = [
    "https://iptv-org.github.io/iptv/index.m3u",
    "https://iptv-org.github.io/iptv/countries/tr.m3u",
    "https://raw.githubusercontent.com/doms9/iptv/refs/heads/default/M3U8/TV.m3u8",
    "https://raw.githubusercontent.com/doms9/iptv/refs/heads/default/M3U8/base.m3u8",
]

OUTPUT_FILE = "playlist.m3u"
EPG_URL = "https://to1un.github.io/iptv-curated/epg.xml.gz"
# Backup raw URL: https://raw.githubusercontent.com/to1un/iptv-curated/main/epg.xml.gz

# Target channels in exact order of appearance
TARGET_CHANNELS = [
    # --- Global & News (English) ---
    {
        "id": "dw_english",
        "name": "DW English (1080p)",
        "pattern": r"DW English \(1080p\)",
        "tvg_id": "Deutsche.Welle.(English).sg",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/75/Deutsche_Welle_symbol_2012.svg/960px-Deutsche_Welle_symbol_2012.svg.png",
    },
    {
        "id": "nhk_world",
        "name": "NHK World-Japan (1080p)",
        "pattern": r"NHK World-Japan \(1080p\)",
        "tvg_id": "NHK.World.–.Japan.(HD).sg",
        "logo": "https://jiotvimages.cdn.jio.com/dare_images/images/NHK_World_Japan.png",
    },
    {
        "id": "trt_world",
        "name": "TRT World (1440p)",
        "direct_url": "https://tv-trtworld.medya.trt.com.tr/master.m3u8",
        "tvg_id": "TRT.WORLD.HD.tr",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/27/TRT_World.svg/960px-TRT_World.svg.png",
    },
    {
        "id": "bloomberg_originals",
        "name": "Bloomberg Originals (1080p)",
        "pattern": r"Bloomberg Originals \(1080p\)",
        "tvg_id": "Bloomberg.Television.(HD).sg",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/56/Bloomberg_Logo.svg/960px-Bloomberg_Logo.svg.png",
    },
    {
        "id": "france24_en",
        "name": "France 24 English (1080p)",
        "pattern": r"France 24 English \(1080p\)",
        "tvg_id": "France.24.Anglais.fr",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/France_24_logo.svg/960px-France_24_logo.svg.png",
    },
    {
        "id": "sky_news",
        "name": "Sky News (1080p)",
        "pattern": r"^Sky News.*1080p|^Sky News$",
        "tvg_id": "Sky.News.HD.uk",
        "logo": "https://upload.wikimedia.org/wikipedia/en/thumb/a/a8/Sky_News_logo_2020.svg/960px-Sky_News_logo_2020.svg.png",
    },
    {
        "id": "aljazeera_en",
        "name": "Al Jazeera English (1080p)",
        "pattern": r"Al Jazeera English \(1080p\)",
        "tvg_id": "AlJazeera.English.net",
        "logo": "https://upload.wikimedia.org/wikipedia/en/thumb/f/f2/Al_Jazeera_English_logo.svg/960px-Al_Jazeera_English_logo.svg.png",
    },
    {
        "id": "cna",
        "name": "CNA (1080p)",
        "pattern": r"CNA \(Singapore\) \(1080p\)",
        "tvg_id": "CNA.(HD).sg",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/63/CNA_%28TV_network%29_logo.svg/960px-CNA_%28TV_network%29_logo.svg.png",
    },

    # --- Movies & Series (English) ---
    {
        "id": "moviesphere",
        "name": "MovieSphere (1080p)",
        "pattern": r"MovieSphere UK \(1080p\)",
        "tvg_id": "Moviesphere.au",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d4/Lionsgate_2019.svg/960px-Lionsgate_2019.svg.png",
    },
    {
        "id": "hbo_zone",
        "name": "HBO Zone (1080p)",
        "pattern": r"^HBO Zone$",
        "tvg_id": "HBO.Zone.HD.us2",
        "logo": "https://schedulesdirect-api20141201-logos.s3.dualstack.us-east-1.amazonaws.com/stationLogos/s18431_dark_360w_270h.png",
    },
    {
        "id": "cinemax",
        "name": "Cinemax (1080p)",
        "pattern": r"^Cinemax$",
        "tvg_id": "Cinemax.HD.us2",
        "logo": "https://raw.githubusercontent.com/tv-logo/tv-logos/refs/heads/main/countries/united-states/cinemax-us.png",
    },
    {
        "id": "cinemax_classics",
        "name": "Cinemax Classics (1080p)",
        "pattern": r"^Cinemax Classics$",
        "tvg_id": "Cinemax.Classics.us2",
        "logo": "https://raw.githubusercontent.com/tv-logo/tv-logos/refs/heads/main/countries/united-states/cinemax-classics-us.png",
    },
    {
        "id": "starz_cinema",
        "name": "Starz Cinema (1080p)",
        "pattern": r"^Starz Cinema$",
        "tvg_id": "Starz.Cinema.HD.us2",
        "logo": "https://schedulesdirect-api20141201-logos.s3.dualstack.us-east-1.amazonaws.com/stationLogos/s67236_dark_360w_270h.png",
    },
    {
        "id": "starz_comedy",
        "name": "Starz Comedy (1080p)",
        "pattern": r"^Starz Comedy$",
        "tvg_id": "Starz.Comedy.HD.us2",
        "logo": "https://schedulesdirect-api20141201-logos.s3.dualstack.us-east-1.amazonaws.com/stationLogos/s34901_dark_360w_270h.png",
    },
    {
        "id": "paramount_network",
        "name": "Paramount Network (1080p)",
        "pattern": r"^Paramount Network$",
        "tvg_id": "Paramount.Network.HD.us2",
        "logo": "http://schedulesdirect-api20141201-logos.s3.dualstack.us-east-1.amazonaws.com/stationLogos/s11163_dark_360w_270h.png",
    },
    {
        "id": "syfy",
        "name": "Syfy (1080p)",
        "pattern": r"^Syfy$",
        "tvg_id": "Syfy.HD.us2",
        "logo": "http://schedulesdirect-api20141201-logos.s3.dualstack.us-east-1.amazonaws.com/stationLogos/s11097_dark_360w_270h.png",
    },
    {
        "id": "ifc",
        "name": "IFC (1080p)",
        "pattern": r"^IFC$",
        "tvg_id": "IFC.HD.us2",
        "logo": "https://schedulesdirect-api20141201-logos.s3.dualstack.us-east-1.amazonaws.com/stationLogos/s14873_dark_360w_270h.png",
    },
    {
        "id": "amc",
        "name": "AMC (720p)",
        "pattern": r"^AMC$",
        "tvg_id": "AMC.HD.us2",
        "logo": "https://schedulesdirect-api20141201-logos.s3.dualstack.us-east-1.amazonaws.com/stationLogos/s10021_dark_360w_270h.png",
    },

    # --- Animation & Classics (English) ---
    {
        "id": "cartoon_network",
        "name": "Cartoon Network (1080p)",
        "pattern": r"^Cartoon Network$",
        "tvg_id": "Cartoon.Network.HD.us2",
        "logo": "https://raw.githubusercontent.com/tv-logo/tv-logos/refs/heads/main/countries/united-states/cartoon-network-us.png",
    },
    {
        "id": "boomerang",
        "name": "Boomerang (1080p)",
        "pattern": r"^Boomerang$",
        "tvg_id": "Boomerang.us2",
        "logo": "https://raw.githubusercontent.com/tv-logo/tv-logos/refs/heads/main/countries/united-states/boomerang-us.png",
    },
    {
        "id": "disney_xd",
        "name": "Disney XD (720p)",
        "pattern": r"^Disney XD$",
        "tvg_id": "Disney.XD.HD.us2",
        "logo": "https://raw.githubusercontent.com/tv-logo/tv-logos/refs/heads/main/countries/united-states/disney-xd-us.png",
    },

    # --- Documentary & Science (English) ---
    {
        "id": "science_channel",
        "name": "Science Channel (1080p)",
        "pattern": r"^Science Channel$",
        "tvg_id": "Science.Channel.HD.us2",
        "logo": "http://schedulesdirect-api20141201-logos.s3.dualstack.us-east-1.amazonaws.com/stationLogos/s24282_dark_360w_270h.png",
    },
    {
        "id": "nat_geo",
        "name": "Nat Geo (720p)",
        "pattern": r"^Nat Geo$",
        "tvg_id": "National.Geographic.HD.us2",
        "logo": "http://schedulesdirect-api20141201-logos.s3.dualstack.us-east-1.amazonaws.com/stationLogos/s49438_dark_360w_270h.png",
    },
    {
        "id": "nat_geo_wild",
        "name": "Nat Geo Wild (720p)",
        "pattern": r"^Nat Geo Wild$",
        "tvg_id": "National.Geographic.Wild.HD.us2",
        "logo": "https://schedulesdirect-api20141201-logos.s3.dualstack.us-east-1.amazonaws.com/stationLogos/s86880_dark_360w_270h.png",
    },
    {
        "id": "animal_planet",
        "name": "Animal Planet (1080p)",
        "pattern": r"^Animal Planet$",
        "tvg_id": "Animal.Planet.HD.us2",
        "logo": "http://schedulesdirect-api20141201-logos.s3.dualstack.us-east-1.amazonaws.com/stationLogos/s16331_dark_360w_270h.png",
    },
    {
        "id": "bbc_america",
        "name": "BBC America (1080p)",
        "pattern": r"^BBC America$",
        "tvg_id": "BBC.America.HD.us2",
        "logo": "http://schedulesdirect-api20141201-logos.s3.dualstack.us-east-1.amazonaws.com/stationLogos/s64492_dark_360w_270h.png",
    },

    # --- Sports (English & TR) ---
    {
        "id": "sky_sports_f1",
        "name": "Sky Sports F1 (720p)",
        "pattern": r"^Sky Sports F1$",
        "tvg_id": "SkySp.F1.uk",
        "logo": "https://raw.githubusercontent.com/tv-logo/tv-logos/refs/heads/main/countries/united-kingdom/sky-sports-f1-icon-uk.png",
    },
    {
        "id": "nba_tv",
        "name": "NBA TV (1080p)",
        "pattern": r"^NBA TV$",
        "tvg_id": "NBA.TV.HD.us2",
        "logo": "http://schedulesdirect-api20141201-logos.s3.dualstack.us-east-1.amazonaws.com/stationLogos/s32281_dark_360w_270h.png",
    },
    {
        "id": "trt_spor",
        "name": "TRT Spor (1440p)",
        "direct_url": "https://tv-trtspor1.medya.trt.com.tr/master.m3u8",
        "tvg_id": "TRT.SPOR.HD.tr",
        "logo": "https://i.imgur.com/6tv0zxh.png",
    },

    # --- National / Turkish ---
    {
        "id": "trt_1",
        "name": "TRT 1 (1440p)",
        "direct_url": "https://tv-trt1.medya.trt.com.tr/master.m3u8",
        "tvg_id": "TRT.1.HD.tr",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/85/TRT_1_logo_%282021-%29.svg/960px-TRT_1_logo_%282021-%29.svg.png",
    },
    {
        "id": "trt_belgesel",
        "name": "TRT Belgesel (1440p)",
        "direct_url": "https://tv-trtbelgesel.medya.trt.com.tr/master.m3u8",
        "tvg_id": "TRT.BELGESEL.HD.tr",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b3/TRT_Belgesel_logo.svg/960px-TRT_Belgesel_logo.svg.png",
    },
    {
        "id": "trt_cocuk",
        "name": "TRT Çocuk (1440p)",
        "direct_url": "https://tv-trtcocuk.medya.trt.com.tr/master.m3u8",
        "tvg_id": "TRT.ÇOCUK.HD.tr",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/TRT_%C3%87ocuk_logo_%282021%29.svg/960px-TRT_%C3%87ocuk_logo_%282021%29.svg.png",
    },
    {
        "id": "tv8",
        "name": "TV8 (1080p)",
        "pattern": r"TV8 \(Turkiye\) \(1080p\)",
        "tvg_id": "TV8.HD.tr",
        "logo": "https://upload.wikimedia.org/wikipedia/tr/thumb/6/68/Tv8_Yeni_Logo.png/960px-Tv8_Yeni_Logo.png",
    },
    {
        "id": "kanal_d",
        "name": "Kanal D (1080p)",
        "pattern": r"Kanal D \(Turkiye\) \(1080p\)",
        "tvg_id": "KANAL.D.HD.tr",
        "logo": "https://i.imgur.com/9o1atM6.png",
    },
    {
        "id": "now_tv",
        "name": "NOW TV (720p)",
        "pattern": r"NOW TV \(720p\)",
        "tvg_id": "FOX.HD.tr",
        "logo": "https://i.imgur.com/5EYjWK7.png",
    },
    {
        "id": "star_tv",
        "name": "Star TV (720p)",
        "pattern": r"Star TV \(Turkiye\) \(720p\)",
        "tvg_id": "STAR.TV.HD.tr",
        "logo": "https://i.imgur.com/9O3DHRB.png",
    },
    {
        "id": "ntv",
        "name": "NTV (720p)",
        "pattern": r"NTV \(Turkiye\)",
        "tvg_id": "NTV.HD.tr",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/NTV_%28Turkey%29_logo.svg/960px-NTV_%28Turkey%29_logo.svg.png",
    },
]


def fetch_source(url: str) -> str:
    print(f"Fetching: {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def parse_m3u_sources(raw_text: str) -> dict[str, tuple[str, str]]:
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
        url_lines = [l for l in lines if l.startswith("http")]
        if not url_lines:
            continue
        url = url_lines[-1]
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

    available_streams = parse_m3u_sources(combined_raw)
    ordered_entries = []

    for item in TARGET_CHANNELS:
        display_name = item["name"]
        logo_url = item.get("logo", "")
        tvg_id = item.get("tvg_id", "")
        stream_url = item.get("direct_url")

        # If not direct URL, search in parsed sources via pattern
        if not stream_url and "pattern" in item:
            pat = re.compile(item["pattern"], re.IGNORECASE)
            for channel_title, (header, url) in available_streams.items():
                if pat.search(channel_title):
                    stream_url = url
                    if not logo_url:
                        m = re.search(r'tvg-logo="([^"]+)"', header)
                        if m:
                            logo_url = m.group(1)
                    break

        if not stream_url:
            print(f"  [-] Failed to resolve stream for: {display_name}", file=sys.stderr)
            continue

        # Build clean #EXTINF line with EPG id and logo
        tvg_attr = f' tvg-id="{tvg_id}"' if tvg_id else ""
        extinf_line = f'#EXTINF:-1{tvg_attr} tvg-logo="{logo_url}",{display_name}'
        ordered_entries.append(f"{extinf_line}\n{stream_url}")
        print(f"  [+] Added: {display_name}")

    if not ordered_entries:
        print("Error: No channels could be matched or resolved.", file=sys.stderr)
        sys.exit(1)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f'#EXTM3U url-tvg="{EPG_URL}"\n\n')
        f.write("\n\n".join(ordered_entries) + "\n")

    print(f"\nSuccessfully created {OUTPUT_FILE} with {len(ordered_entries)} channels in ordered sequence.")

    # Generate matching EPG guide
    try:
        import build_epg
        build_epg.main()
    except Exception as err:
        print(f"Warning: Failed to run build_epg: {err}", file=sys.stderr)


if __name__ == "__main__":
    main()
