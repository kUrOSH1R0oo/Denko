# Tansa: Advanced Web Crawler
Tansa is an advanced web crawler designed to automatically navigate through websites, extract and categorize links, and provide a structured view of the web content. With its ability to handle multi-threaded operations, Tansa is a powerful tool for web scraping, site analysis, and link discovery.

## Features
   - **Internal and External URL Extraction**: Differentiates between internal (within the same domain) and external (outside the domain) URLs.
   - **Multi-threaded Operation**: Speeds up the crawling process by using multiple threads.
   - **Results Saving**: Optionally saves the extracted URLs to separate text files for internal and external links.
   - **Customizable User-Agent**: Allows you to specify a custom User-Agent string for HTTP requests.

## Installation
1. Clone the repository
   ```bash
   git clone https://github.com/z33phyr/Tansa
   ```
2. Install the essential libraries
   ```bash
   pip3 install -r requirements.txt
   ```
3. Run Tansa
   ```bash
   python3 tansa.py
   ```
   
## Usage
To run Tansa, execute the script from the command line with the desired parameters. Here's the general syntax:
  ```bash
  python3 tansa.py URL <options>
  ```

## Parameters
  - **url (required)**: The base URL to start the web crawling process.
  - **-m, --max-urls**: Maximum number of URLs to crawl (default: 30).
  - **-d, --max-depth**: Maximum depth level for crawling (default: 3).
  - **-t, --threads**: Number of threads for concurrent crawling (default: 4).
  - **-s, --save**: Option to save results to files ("yes" or "no", default: "no").
  - **-a, --user-agent**: Custom User-Agent string for requests.
  ```bash
  python3 tansa.py http://example.com -m 50 -d 4 -t 6 -s yes -a "CustomUserAgent/1.0"
  ```

## License
   - Tansa is licensed under GNU General Public License

## Author
   - Zephyr
