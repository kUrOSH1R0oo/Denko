require 'bundler/setup'
Bundler.require(:default)
require 'bundler/setup'
require 'net/http'
require 'uri'
require 'thread'
require 'optparse'
require 'set'

BANNER = <<~BANNER
░       ░░░        ░░   ░░░  ░░  ░░░░  ░░░      ░░
▒  ▒▒▒▒  ▒▒  ▒▒▒▒▒▒▒▒    ▒▒  ▒▒  ▒▒▒  ▒▒▒  ▒▒▒▒  ▒
▓  ▓▓▓▓  ▓▓      ▓▓▓▓  ▓  ▓  ▓▓     ▓▓▓▓▓  ▓▓▓▓  ▓
█  ████  ██  ████████  ██    ██  ███  ███  ████  █
█       ███        ██  ███   ██  ████  ███      ██
                                    ~ A1SBERG
BANNER

class Tansa
  attr_accessor :base_url, :max_urls, :max_depth, :num_threads, :user_agent
  def initialize(base_url, max_urls: 30, max_depth: 3, num_threads: 4, user_agent: nil)
    @base_url = base_url
    @max_urls = max_urls
    @max_depth = max_depth
    @num_threads = num_threads
    @user_agent = user_agent
    @internal_urls = Set.new
    @external_urls = Set.new
    @total_urls_visited = 0
    @queue = Queue.new
    setup_session
    at_exit do
      save_results_to_file
    end
  end

  def setup_session
    @user_agent ||= "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
  end

  def get_robots_txt(url)
    uri = URI.join(url, '/robots.txt')
    response = Net::HTTP.get_response(uri)
    response.is_a?(Net::HTTPSuccess) ? response.body : nil
  rescue
    nil
  end

  def can_fetch?(url, robots_txt)
    return true unless robots_txt
    uri = URI.parse(url)
    user_agent_pattern = /^User-agent: .*$/i
    disallow_pattern = /^Disallow: .+$/i
    user_agent_section = robots_txt.match(user_agent_pattern)&.end(0)
    if user_agent_section
      disallow_section = robots_txt[user_agent_section..-1].scan(disallow_pattern).map { |line| line.split(':', 2).last.strip }
      disallow_section.any? { |path| uri.path.start_with?(path) } ? false : true
    else
      true
    end
  end

  def fetch(url)
    uri = URI.parse(url)
    Net::HTTP.start(uri.host, uri.port, use_ssl: (uri.scheme == 'https')) do |http|
      request = Net::HTTP::Get.new(uri.request_uri, {'User-Agent' => @user_agent})
      response = http.request(request)
      response.body
    end
  rescue => e
    puts "Failed to fetch #{url} - #{e.message}"
    nil
  end

  def parallel_fetch(urls)
    results = Concurrent::Hash.new
    futures = urls.map do |url|
      Concurrent::Promise.execute do
        results[url] = fetch(url)
      end
    end
    Concurrent::Promise.zip(*futures).value!
    results
  end

  def get_all_website_links(url, domain_name, depth)
    urls = Set.new
    return urls if depth > @max_depth
    document = Nokogiri::HTML(parallel_fetch([url])[url])
    robots_txt = get_robots_txt(url)
    return urls unless can_fetch?(url, robots_txt)
    document.css('a').each do |a_tag|
      href = a_tag['href']
      next unless href
      href = URI.join(url, href).to_s
      next unless valid?(href)
      href = URI.parse(href).normalize.to_s
      if @internal_urls.include?(href) || @external_urls.include?(href)
        next
      end
      if !href.include?(domain_name)
        puts "#{href}"
        @external_urls.add(href)
        next
      end
      puts "#{href}"
      urls.add(href)
      @internal_urls.add(href)
    end
    urls
  rescue
    puts "#{url}"
    urls
  end

  def valid?(url)
    uri = URI.parse(url)
    uri.host && uri.scheme
  end

  def worker
    until @total_urls_visited >= @max_urls
      url, depth = @queue.pop
      @total_urls_visited += 1
      puts "#{url}"
      links = get_all_website_links(url, URI.parse(url).host, depth)
      links.each do |link|
        break if @total_urls_visited >= @max_urls
        @queue.push([link, depth + 1])
      end
    end
  end

  def save_results_to_file
    domain_name = URI.parse(@base_url).host
    File.open("#{domain_name}_in-domain.txt", 'w') do |f|
      @internal_urls.each { |link| f.puts(link) }
    end
    File.open("#{domain_name}_third-party.txt", 'w') do |f|
      @external_urls.each { |link| f.puts(link) }
    end
  end

  def crawl
    @queue.push([@base_url, 0])
    threads = Array.new(@num_threads) { Thread.new { worker } }
    threads.each(&:join)
    puts "[+] Total In-Domain links: #{@internal_urls.size}"
    puts "[+] Total Third-Party links: #{@external_urls.size}"
    puts "[+] Total URLs: #{@internal_urls.size + @external_urls.size}"
    puts "[+] Total Crawled URLs: #{@total_urls_visited}"
  end
end

options = {}
OptionParser.new do |opts|
  puts BANNER, "\n"
  opts.banner = "Usage: denko.rb [options]"
  opts.on("-uURL", "--url=URL", "The URL to extract links from.") { |v| options[:url] = v }
  opts.on("-mNUM", "--max-urls=NUM", Integer, "Number of max URLs to crawl, default is 30.") { |v| options[:max_urls] = v }
  opts.on("-dNUM", "--max-depth=NUM", Integer, "Max depth to crawl, default is 3.") { |v| options[:max_depth] = v }
  opts.on("-tNUM", "--threads=NUM", Integer, "Number of threads to use, default is 4.") { |v| options[:num_threads] = v }
  opts.on("-aAGENT", "--user-agent=AGENT", "Custom User-Agent to use for requests.") { |v| options[:user_agent] = v }
end.parse!
if options[:url].nil?
  puts "[-] URL is required"
  exit 1
end
crawler = Tansa.new(
  options[:url],
  max_urls: options[:max_urls] || 30,
  max_depth: options[:max_depth] || 3,
  num_threads: options[:num_threads] || 4,
  user_agent: options[:user_agent]
)
start_time = Time.now
crawler.crawl
