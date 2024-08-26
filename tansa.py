import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import re
import argparse
import threading
import queue
from datetime import datetime

banner = r"""
 ___________   __      _____  ___    ________     __
("     _   ") /""\    (\"   \|"  \  /"       )   /""\
 )__/  \\__/ /    \   |.\\   \    |(:   \___/   /    \
    \\_ /   /' /\  \  |: \.   \\  | \___  \    /' /\  \
    |.  |  //  __'  \ |.  \    \. |  __/  \\  //  __'  \
    \:  | /   /  \\  \|    \    \ | /" \   :)/   /  \\  \
     \__|(___/    \___)\___|\____\)(_______/(___/    \___)
                                            Zephyr
"""

class Tansa:
    def __init__(self, base_url, max_urls=30, max_depth=3, num_threads=4, save_results=False, user_agent=None):
        self.base_url = base_url
        self.max_urls = max_urls
        self.max_depth = max_depth
        self.num_threads = num_threads
        self.save_results = save_results
        self.user_agent = user_agent
        self.internal_urls = set()
        self.external_urls = set()
        self.total_urls_visited = 0
        self.session = requests.Session()
        self.setup_session()

    def setup_session(self):
        DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        user_agent = self.user_agent or DEFAULT_USER_AGENT
        self.session.headers.update({
            "User-Agent": user_agent
        })

    def get_robots_txt(self, url):
        parsed_url = urlparse(url)
        robots_url = urljoin(f"{parsed_url.scheme}://{parsed_url.netloc}", "/robots.txt")
        try:
            response = self.session.get(robots_url)
            response.raise_for_status()
            return response.text
        except requests.RequestException:
            return None

    def can_fetch(self, url, robots_txt):
        if not robots_txt:
            return True
        parsed_url = urlparse(url)
        user_agent_pattern = re.compile(r'^User-agent: .*$', re.MULTILINE)
        disallow_pattern = re.compile(r'^Disallow: .+$', re.MULTILINE)
        user_agent_section = user_agent_pattern.search(robots_txt)
        if user_agent_section:
            user_agent_section = user_agent_section.end()
            disallow_section = disallow_pattern.findall(robots_txt[user_agent_section:])
            for disallow in disallow_section:
                path = disallow.split(':', 1)[1].strip()
                if parsed_url.path.startswith(path):
                    return False
        return True

    def get_all_website_links(self, url, domain_name, depth):
        urls = set()
        if depth > self.max_depth:
            return urls
        try:
            response = self.session.get(url, allow_redirects=True)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            robots_txt = self.get_robots_txt(url)
            if not self.can_fetch(url, robots_txt):
                print(f"[!] Skipping URL due to robots.txt: {url}")
                return urls
            for a_tag in soup.find_all("a"):
                href = a_tag.get("href")
                if not href:
                    continue
                href = urljoin(url, href)
                parsed_href = urlparse(href)
                href = f"{parsed_href.scheme}://{parsed_href.netloc}{parsed_href.path}"
                if not self.is_valid(href):
                    continue
                if href in self.internal_urls or href in self.external_urls:
                    continue
                if domain_name not in href:
                    print(f"[!] External: {href}")
                    self.external_urls.add(href)
                    continue
                print(f"[*] Internal: {href}")
                urls.add(href)
                self.internal_urls.add(href)
        except requests.RequestException as e:
            print(f"[!] Failed to retrieve {url}: {e}")
        return urls

    def is_valid(self, url):
        parsed = urlparse(url)
        return bool(parsed.netloc) and bool(parsed.scheme)

    def worker(self, q):
        while True:
            url, depth = q.get()
            if self.total_urls_visited >= self.max_urls:
                q.task_done()
                break
            self.total_urls_visited += 1
            print(f"[*] Crawling: {url} (Depth: {depth})")
            links = self.get_all_website_links(url, urlparse(url).netloc, depth)
            for link in links:
                if self.total_urls_visited >= self.max_urls:
                    break
                q.put((link, depth + 1))
            q.task_done()

    def save_results_to_file(self):
        domain_name = urlparse(self.base_url).netloc
        with open(f"{domain_name}_internal.txt", "w") as f:
            for internal_link in self.internal_urls:
                f.write(internal_link.strip() + "\n")
        with open(f"{domain_name}_external.txt", "w") as f:
            for external_link in self.external_urls:
                f.write(external_link.strip() + "\n")

    def crawl(self):
        q = queue.Queue()
        q.put((self.base_url, 0))
        threads = []
        for _ in range(self.num_threads):
            t = threading.Thread(target=self.worker, args=(q,))
            t.start()
            threads.append(t)
        q.join()
        for t in threads:
            t.join()
        if self.save_results:
            self.save_results_to_file()
        print(f"[+] Total Internal links: {len(self.internal_urls)}")
        print(f"[+] Total External links: {len(self.external_urls)}")
        print(f"[+] Total URLs: {len(self.external_urls) + len(self.internal_urls)}")
        print(f"[+] Total crawled URLs: {self.total_urls_visited}")

if __name__ == "__main__":
    print(banner)
    parser = argparse.ArgumentParser(description="Tansa: Advanced Web Crawler Tool")
    parser.add_argument("url", help="The URL to extract links from.")
    parser.add_argument("-m", "--max-urls", help="Number of max URLs to crawl, default is 30.", default=30, type=int)
    parser.add_argument("-d", "--max-depth", help="Max depth to crawl, default is 3.", default=3, type=int)
    parser.add_argument("-t", "--threads", help="Number of threads to use, default is 4.", default=4, type=int)
    parser.add_argument("-s", "--save", help="Save results to files (yes/no), default is no.", default="no", choices=["yes", "no"])
    parser.add_argument("-a", "--user-agent", help="Custom User-Agent to use for requests.")
    args = parser.parse_args()
    url = args.url
    max_urls = args.max_urls
    max_depth = args.max_depth
    num_threads = args.threads
    save_results = args.save == "yes"
    user_agent = args.user_agent
    crawler = Tansa(
            base_url=url,
            max_urls=max_urls,
            max_depth=max_depth,
            num_threads=num_threads,
            save_results=save_results,
            user_agent=user_agent
    )
    start_time = datetime.now()
    crawler.crawl()
    print(f"[+] Crawling completed in {datetime.now() - start_time}")
