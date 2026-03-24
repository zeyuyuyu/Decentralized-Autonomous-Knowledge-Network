import asyncio
from kademlia.network import Server
from urllib.parse import urlparse
import aiohttp
import hashlib
import json

class CrawlerNode:
    def __init__(self, bootstrap_nodes=None, port=8468):
        self.port = port
        self.bootstrap_nodes = bootstrap_nodes or []
        self.dht = Server()
        self.discovered_content = set()
        self.is_running = False

    async def start(self):
        """Start the crawler node and connect to DHT network"""
        await self.dht.listen(self.port)
        if self.bootstrap_nodes:
            await self.dht.bootstrap(self.bootstrap_nodes)
        self.is_running = True
        
    async def crawl_url(self, url):
        """Crawl a URL and store its content hash in the DHT"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        content_hash = hashlib.sha256(content.encode()).hexdigest()
                        
                        # Store URL -> content hash mapping in DHT
                        await self.dht.set(url, content_hash)
                        
                        # Store content hash -> metadata mapping
                        metadata = {
                            'url': url,
                            'timestamp': str(asyncio.get_event_loop().time()),
                            'title': self._extract_title(content)
                        }
                        await self.dht.set(content_hash, json.dumps(metadata))
                        
                        self.discovered_content.add(url)
                        return content_hash
        except Exception as e:
            print(f'Error crawling {url}: {str(e)}')
            return None

    async def discover_content(self, search_key):
        """Query DHT network for content matching search key"""
        try:
            content_hash = await self.dht.get(search_key)
            if content_hash:
                metadata = await self.dht.get(content_hash)
                if metadata:
                    return json.loads(metadata)
        except Exception as e:
            print(f'Error discovering content: {str(e)}')
        return None

    def _extract_title(self, html_content):
        """Extract title from HTML content"""
        try:
            start = html_content.find('<title>')
            end = html_content.find('</title>')
            if start != -1 and end != -1:
                return html_content[start+7:end].strip()
        except:
            pass
        return ''

    async def stop(self):
        """Stop the crawler node"""
        self.is_running = False
        self.dht.stop()

    async def get_network_stats(self):
        """Get statistics about the DHT network"""
        return {
            'node_id': self.dht.node.long_id,
            'peers': len(self.dht.protocol.router.buckets),
            'discovered_urls': len(self.discovered_content)
        }

    def __str__(self):
        return f'CrawlerNode(port={self.port}, running={self.is_running})'