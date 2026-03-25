import requests
from bs4 import BeautifulSoup
import hashlib
import json
import time
import random

class CrawlerNode:
    def __init__(self, seed_urls, max_depth=3, max_pages=1000, delay=1):
        self.seed_urls = seed_urls
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.delay = delay
        self.visited_urls = set()
        self.page_index = {}

    def crawl(self):
        queue = self.seed_urls.copy()
        depth = 0

        while queue and depth < self.max_depth and len(self.page_index) < self.max_pages:
            depth += 1
            new_queue = []

            for url in queue:
                if url not in self.visited_urls:
                    self.visited_urls.add(url)
                    try:
                        response = requests.get(url)
                        soup = BeautifulSoup(response.content, 'html.parser')
                        content = soup.get_text()
                        page_hash = hashlib.sha256(content.encode()).hexdigest()
                        self.page_index[page_hash] = {
                            'url': url,
                            'content': content
                        }

                        for link in soup.find_all('a'):
                            new_url = link.get('href')
                            if new_url and new_url.startswith('http'):
                                new_queue.append(new_url)
                    except:
                        pass

                    time.sleep(self.delay + random.uniform(0, 1))

            queue = new_queue

        return self.page_index

if __name__ == '__main__':
    seed_urls = ['https://en.wikipedia.org', 'https://www.github.com', 'https://www.reddit.com']
    crawler = CrawlerNode(seed_urls)
    index = crawler.crawl()
    print(json.dumps(index, indent=2))
