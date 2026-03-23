import asyncio
import hashlib
from typing import Dict, Set, List
from dataclasses import dataclass
import aiohttp
import time

@dataclass
class CrawlTask:
    url: str
    depth: int
    timestamp: float
    owner_id: str

class CrawlerNode:
    def __init__(self, node_id: str, peers: List[str], max_depth: int = 3):
        self.node_id = node_id
        self.peers = set(peers)
        self.max_depth = max_depth
        self.active_tasks: Dict[str, CrawlTask] = {}
        self.completed_urls: Set[str] = set()
        self.session = None

    def task_id(self, url: str) -> str:
        return hashlib.sha256(url.encode()).hexdigest()

    async def start(self):
        self.session = aiohttp.ClientSession()
        await asyncio.gather(
            self.run_crawler(),
            self.run_gossip_protocol()
        )

    async def run_crawler(self):
        while True:
            for task_id, task in list(self.active_tasks.items()):
                if task.owner_id == self.node_id:
                    try:
                        async with self.session.get(task.url) as response:
                            if response.status == 200:
                                text = await response.text()
                                # Process links and create new tasks
                                if task.depth < self.max_depth:
                                    new_urls = self.extract_links(text)
                                    await self.add_tasks(new_urls, task.depth + 1)
                    except Exception as e:
                        print(f"Error crawling {task.url}: {e}")
                    finally:
                        self.completed_urls.add(task.url)
                        del self.active_tasks[task_id]
            await asyncio.sleep(1)

    async def run_gossip_protocol(self):
        while True:
            for peer in self.peers:
                try:
                    async with self.session.post(f"{peer}/sync", 
                            json={
                                "tasks": self.active_tasks,
                                "completed": list(self.completed_urls)
                            }) as response:
                        if response.status == 200:
                            data = await response.json()
                            self.merge_state(data)
                except Exception as e:
                    print(f"Error syncing with peer {peer}: {e}")
            await asyncio.sleep(5)

    def merge_state(self, peer_state: dict):
        """Merge peer state with local state using timestamp resolution"""
        for task_id, task in peer_state["tasks"].items():
            if task_id not in self.active_tasks or \
               task.timestamp > self.active_tasks[task_id].timestamp:
                self.active_tasks[task_id] = task
        
        self.completed_urls.update(peer_state["completed"])

    async def add_tasks(self, urls: List[str], depth: int):
        """Add new crawl tasks if not already completed/active"""
        timestamp = time.time()
        for url in urls:
            task_id = self.task_id(url)
            if url not in self.completed_urls and task_id not in self.active_tasks:
                self.active_tasks[task_id] = CrawlTask(
                    url=url,
                    depth=depth,
                    timestamp=timestamp,
                    owner_id=self.node_id
                )

    def extract_links(self, html: str) -> List[str]:
        """Extract links from HTML content"""
        # Implementation of link extraction logic
        # Returns list of normalized URLs
        return []

    async def close(self):
        if self.session:
            await self.session.close()