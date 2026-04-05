import re
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from typing import List
from scraper.core.base_spider import BaseSpider
from scraper.models import MediaItem, MagnetItem
from urllib.parse import urljoin

class MikanSpider(BaseSpider):
    BASE_URL = "https://mikan.tangbai.cc"
    # Provide a standard browser User-Agent to avoid blocking
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }

    @property
    def site_id(self) -> str:
        return "mikan"

    def search_media(self, keyword: str) -> List[MediaItem]:
        search_url = f"{self.BASE_URL}/Home/Search?searchstr={keyword}"
        res = requests.get(search_url, headers=self.HEADERS, timeout=15)
        res.raise_for_status()

        soup = BeautifulSoup(res.text, "lxml")
        media_items = []
        seen_ids = set()

        subgroups = []
        for sub_a in soup.select('a[data-subgroupid]'):
            sub_id = sub_a.get('data-subgroupid', '').strip()
            sub_name = sub_a.get_text(strip=True)
            if sub_id and sub_name and sub_name != "显示全部" and sub_name != "顯示全部":
                subgroups.append((sub_id, sub_name))

        unique_subgroups = []
        seen_subs = set()
        for s in subgroups:
            if s[0] not in seen_subs:
                seen_subs.add(s[0])
                unique_subgroups.append(s)

        # Mikan search groups episodes under a banner holding the Bangumi's title and link.
        # Often links to bangumi look like <a href="/Home/Bangumi/3141" ...>Title</a>
        for a_tag in soup.select('a[href^="/Home/Bangumi/"]'):
            href = a_tag.get('href')
            title = a_tag.get_text(strip=True)
            if not title:
                # sometimes they put an image inside the a_tag, or use title attribute
                title = a_tag.get('title', '').strip()
            
            if not title:
                continue

            # Extract bgm_id from /Home/Bangumi/ID
            match = re.search(r'/Home/Bangumi/(\d+)', href)
            if match:
                bgm_id = match.group(1)
                if bgm_id not in seen_ids:
                    seen_ids.add(bgm_id)
                    
                    # 1. Add the all-inclusive bangumi item
                    media_items.append(
                        MediaItem(
                            media_id=bgm_id,
                            name=f"{title} (全部)",
                            url=urljoin(self.BASE_URL, href),
                            cover_image=None, 
                            site=self.site_id
                        )
                    )
                    
                    # 2. Add each subgroup for this bangumi
                    for sub_id, sub_name in unique_subgroups:
                        media_items.append(
                            MediaItem(
                                media_id=bgm_id,
                                name=f"{title} [{sub_name}]",
                                url=urljoin(self.BASE_URL, href),
                                cover_image=None,
                                site=self.site_id,
                                subgroup_id=sub_id,
                                subgroup_name=sub_name
                            )
                        )

        return media_items

    def get_episodes(self, media_id: str, subgroup_id: str = None) -> List[MagnetItem]:
        rss_url = f"{self.BASE_URL}/RSS/Bangumi?bangumiId={media_id}"
        if subgroup_id:
            rss_url += f"&subgroupid={subgroup_id}"

        res = requests.get(rss_url, headers=self.HEADERS, timeout=15)
        res.raise_for_status()

        try:
            root = ET.fromstring(res.content)
        except ET.ParseError:
            return []

        episodes = []
        for item in root.findall('./channel/item'):
            title = item.findtext('title') or ""
            publish_time = item.findtext('pubDate') or ""
            link = item.findtext('link') or ""
            
            torrent_url = None
            magnet_url = None
            file_size_mb = None

            enclosure = item.find('enclosure')
            if enclosure is not None:
                torrent_url = enclosure.get('url')
                length_bytes = enclosure.get('length')
                if length_bytes and length_bytes.isdigit():
                    file_size_mb = round(int(length_bytes) / (1024 * 1024), 2)
                    
                # Extract hash from torrent_url e.g. /Download/20260116/091b1b30d24c4d41759da1b0e24ddfffc89925c4.torrent
                if torrent_url:
                    match = re.search(r'/([0-9a-fA-F]{40})\.torrent$', torrent_url)
                    if match:
                        magnet_url = f"magnet:?xt=urn:btih:{match.group(1)}"

            episodes.append(
                MagnetItem(
                    title=title,
                    torrent_url=torrent_url,
                    magnet_url=magnet_url,
                    publish_time=publish_time,
                    file_size_mb=file_size_mb,
                    site=self.site_id
                )
            )

        return episodes
