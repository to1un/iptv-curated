#!/usr/bin/env python3
"""
IPTV Curated Playlist Generator
Fetches sources from iptv-org, filters desired channels, strips all group metadata (flat list),
and outputs a clean, auto-updating playlist.m3u.
"""

import re
import sys
import urllib.request

# Sources to fetch channels from
SOURCES = [
    "https://iptv-org.github.io/iptv/index.m3u",
]

# Targeted channel display names (case-insensitive substring or regex)
# Currently set to only 1 channel for initial testing
TARGET_CHANNELS = [
    "NHK World-Japan",
]

OUTPUT_FILE = "playlist.m3u"


def fetch_playlist(url: str) -> str:
    print(f"Fetching source: {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read().decode("utf-8", errors="ignore")


def parse_and_filter(raw_m3u: str) -> list[tuple[str, str]]:
    """
    Parses an M3U content string, matches target channels,
    removes group-title attribute (for flat ungrouped display),
    and returns a list of (extinf_header, stream_url).
    """
    results = []
    found_targets = set()

    # Split into entries starting with #EXTINF
    chunks = raw_m3u.split("#EXTINF:")
    for chunk in chunks[1:]:
        lines = [line.strip() for line in chunk.strip().split("\n") if line.strip()]
        if len(lines) < 2:
            continue

        extinf_line = "#EXTINF:" + lines[0]
        # Last line is the stream URL, intermediate lines might be #EXTVLCOPT
        stream_url = lines[-1]
        options = [line for line in lines[1:-1] if line.startswith("#EXT")]

        # Extract channel name (everything after the last comma in #EXTINF line)
        parts = extinf_line.split(",", 1)
        if len(parts) < 2:
            continue
        channel_name = parts[1].strip()

        for target in TARGET_CHANNELS:
            # Match channel name
            pattern = re.compile(rf"\b{re.escape(target)}\b", re.IGNORECASE)
            if pattern.search(channel_name):
                # Avoid duplicates: take the first working/best matching stream
                if target in found_targets:
                    continue

                # Strip group-title="..." attribute completely to prevent grouping
                clean_header = re.sub(r'\s*group-title="[^"]*"', '', extinf_line)

                # Assemble complete entry block
                entry_lines = [clean_header]
                if options:
                    entry_lines.extend(options)
                entry_lines.append(stream_url)

                results.append("\n".join(entry_lines))
                found_targets.add(target)
                print(f"  [+] Matched: {target} -> {channel_name}")
                break

    return results


def main():
    all_matched_entries = []

    for source_url in SOURCES:
        try:
            raw_data = fetch_playlist(source_url)
            entries = parse_and_filter(raw_data)
            all_matched_entries.extend(entries)
        except Exception as err:
            print(f"Error fetching {source_url}: {err}", file=sys.stderr)

    if not all_matched_entries:
        print("Warning: No target channels were matched! Existing playlist not overwritten.", file=sys.stderr)
        sys.exit(1)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n\n")
        f.write("\n\n".join(all_matched_entries) + "\n")

    print(f"Successfully generated {OUTPUT_FILE} with {len(all_matched_entries)} channel(s).")


if __name__ == "__main__":
    main()
