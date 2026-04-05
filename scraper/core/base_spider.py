from abc import ABC, abstractmethod
from typing import List
from scraper.models import MediaItem, MagnetItem

class BaseSpider(ABC):
    @property
    @abstractmethod
    def site_id(self) -> str:
        """
        Return the unique identifier for the site (e.g. 'mikan')
        """
        pass

    @abstractmethod
    def search_media(self, keyword: str) -> List[MediaItem]:
        """
        Search for MediaItems by keyword.
        Returns a list of MediaItems matching the keyword.
        """
        pass

    @abstractmethod
    def get_episodes(self, media_id: str, subgroup_id: str = None) -> List[MagnetItem]:
        """
        Fetch magnet items for a specific Media ID and optional subgroup ID.
        """
        pass
