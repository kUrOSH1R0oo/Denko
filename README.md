# Denko Web Crawler
Denko is a web crawler designed to automatically navigate through websites, extract and categorize links, and provide a structured view of the web content. With its ability to handle multi-threaded operations, Denko is a powerful tool for web scraping, site analysis, and link discovery.

## Features
   - **Internal and External URL Extraction**: Differentiates between internal (within the same domain) and external (outside the domain) URLs.
   - **Multi-threaded Operation**: Speeds up the crawling process by using multiple threads.
   - **Results Saving**: Optionally saves the extracted URLs to separate text files for internal and external links.
   - **Customizable User-Agent**: Allows you to specify a custom User-Agent string for HTTP requests.

## Installation
   1. Clone the repository
      ```bash
      git clone https://github.com/Kuraiyume/Denko
      ```
   2. Install the essential gems
      ```bash
      bundle install
      ```
   3. Run Denko
      ```bash
      ruby denko.py -h
      ```

## Parameters
  - **-u (required)**: The base URL to start the web crawling process.
  - **-m, --max-urls**: Maximum number of URLs to crawl (default: 30).
  - **-d, --max-depth**: Maximum depth level for crawling (default: 3).
  - **-t, --threads**: Number of threads for concurrent crawling (default: 4).
  - **-a, --user-agent**: Custom User-Agent string for requests.
  ```bash
  ruby denko.rb -u http://example.com -m 50 -d 4 -t 6 -a "CustomUserAgent/1.0"
  ```

## License
   - Denko is licensed under GNU General Public License

## Author
   - Kuroshiro (A1SBERG)
