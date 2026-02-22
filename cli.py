import argparse
import asyncio
import json
import os
import re
import aiohttp
import feedparser
from datetime import datetime
from loguru import logger

DB_FILE = "status_history.json"
FEEDS = ["https://status.openai.com/history.atom"]

class BolnaPulse:
    def __init__(self):
        self.history = self._load_history()
        self.seen_ids = {entry['id'] for entry in self.history}
        self.cache = {url: {"etag": None} for url in FEEDS}

    # --- Persistence Layer (No DB required) ---
    def _load_history(self):
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r") as f:
                return json.load(f)
        return []

    def _save_to_history(self, entry_data):
        self.history.append(entry_data)
        with open(DB_FILE, "w") as f:
            json.dump(self.history, f, indent=4)

    # --- Processing Logic ---
    def clean_text(self, html):
        return re.sub(r"<[^>]+>", "", html).strip()

    def get_color(self, title):
        """Maps incident severity to status colors."""
        title = title.lower()
        if any(word in title for word in ["down", "outage", "critical"]): return "red"
        if any(word in title for word in ["latency", "degraded", "issue"]): return "yellow"
        return "green"

    # --- The Listener (Asynchronous) ---
    async def fetch_update(self, session, url):
        headers = {"If-None-Match": self.cache[url]["etag"]} if self.cache[url]["etag"] else {}
        try:
            async with session.get(url, headers=headers, timeout=10) as resp:
                if resp.status == 304: return None
                if resp.status == 200:
                    self.cache[url]["etag"] = resp.headers.get("ETag")
                    return feedparser.parse(await resp.text())
        except Exception as e:
            logger.error(f"Fetch error: {e}")
        return None

    async def listen(self):
        logger.info(f"🚀 Pulse Monitor Active: Watching {len(FEEDS)} feeds...")
        async with aiohttp.ClientSession() as session:
            while True:
                for url in FEEDS:
                    feed = await self.fetch_update(session, url)
                    if feed:
                        for entry in feed.entries:
                            eid = entry.get("id")
                            if eid not in self.seen_ids:
                                status_msg = self.clean_text(entry.get("summary", "No details"))
                                data = {
                                    "id": eid,
                                    "date": datetime.now().strftime("%d%m%Y"),
                                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    "title": entry.get("title"),
                                    "status": status_msg[:200],
                                    "color": self.get_color(entry.get("title"))
                                }
                                if self.seen_ids:
                                    print(f"\n🚨 NEW UPDATE: {data['timestamp']} | {data['title']}")
                                self._save_to_history(data)
                                self.seen_ids.add(eid)
                await asyncio.sleep(60)

    # --- The CLI Interface ---
    def run_cli(self):
        parser = argparse.ArgumentParser(description="Bolna Status Intelligence CLI")
        subparsers = parser.add_subparsers(dest="command")

        subparsers.add_parser("listen", help="Start continuous real-time monitoring")
        subparsers.add_parser("all", help="Show all historical incidents")
        subparsers.add_parser("pulse", help="Check system heartbeat")
        
        range_p = subparsers.add_parser("range", help="Get incidents by date range (DDMMYYYY)")
        range_p.add_argument("start")
        range_p.add_argument("end")

        filter_p = subparsers.add_parser("filter", help="Filter by severity")
        filter_p.add_argument("color", choices=["green", "yellow", "red"])

        args = parser.parse_args()

        if args.command == "listen":
            asyncio.run(self.listen())
        elif args.command == "all":
            for e in self.history: print(f"[{e['timestamp']}] {e['title']} ({e['color'].upper()})")
        elif args.command == "range":
            for e in self.history:
                if int(args.start) <= int(e['date']) <= int(args.end):
                    print(f"[{e['timestamp']}] {e['title']}")
        elif args.command == "filter":
            for e in [x for x in self.history if x['color'] == args.color]:
                print(f"[{e['timestamp']}] {e['title']}")

if __name__ == "__main__":
    BolnaPulse().run_cli()