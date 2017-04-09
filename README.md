# NU PageRank

This project aims to

1. crawl all webpages in NU,


2. build a network graph of their inter-connections,
3. identify the important ones using the PageRank algorithm,
4. find other interesting stuff!

### Scraper.py

To limit the total number of pages to analyze, I am limiting the scope to only pages with domain name ending with `northwestern.edu` . My estimation was that there are ~1,000,000 NU pages, small enough to fit in memory as a set so I can easily check whether the page is visited or not (turns out there are much more! Especially the libraries really have a large set of pages with digitalized collection). Some NU related pages/websites may have different domain names and they are ignored for now. Note this code can be easily modified to scrap pages with other domains or a set of domains.

This program only analyzes text pages, such as HTML pages or pages returned by PHP. Otherwise, it will waste lots of time on urls that are large in size but contain no outgoing url, i.e. pictures, videos, pdf documents etc. I tried to exclude some of them using both the file extension and the HTTP response type.

Multi threads are used because url requests and responses take a long time when scraping the internet. I am using 4 threads with a central task queue.

Parsing urls on the internet turns out much harder than I expected. The url standard is actually a very loose constraint. There are so many unexpected url parsing problems. For example, you may or may not include `http://` in your url; an url point to a directory can end with or without `/`; you can specify an url with relative directory starting from `../` so an identical url may appear as `example.com/b` or `example.com/a/../b`. This is a big problem since I need a more uniform format for urls to remember the urls (strings actually) I have visited. Originally I was trying to manually write a long if statement to handle all those cases. Then I realized that the browsers can handle almost all problems so there must be an existing library for this! In the end, I used `urlparse.urljoin` to combine partial urls with the starting url, and `w3lib.url.canonicalize_url` to have a uniform style from all urls. Still, there are some bad urls that I need to process manually. Someone used url `/http://example.com` and someone else used `<a href = " example.com ">` in html. Also, the `example.com` and `example.com/` difference is not handled.

Another big problem is url queries, especially on sites that provide a search function. At an initial test, my bot entered one of that site and got stuck inside the infinite loop of automatically generated urls. Turns out there is a neat way to avoid those websites. The answer is, they also want to avoid all the bots to use their resources! So I can simply visit the `robots.txt` file on those sites, and use `RobotFileParser.can_fetch(url)` to determine whether I should visit that url.

### Url network

This is pretty straight forward. For each page, I find all links identified as `<a href=url>`, then record it as an entry `from_url	[to_url1, to_url2...]`.

Many urls involve redirection. In this program, I only considered the requested url `A` and returned url `B`, and treated that as a link from `A` to `B`. It might be better to add a post-process to label them as identical url.

More work going on … 