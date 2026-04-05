from scraper.core.factory import SpiderFactory
from scraper.strategies.mikan_spider import MikanSpider
from scraper.models import MediaItem, MagnetItem

# Initialize and register spiders
SpiderFactory.register(MikanSpider())

__all__ = ["SpiderFactory", "MediaItem", "MagnetItem"]
