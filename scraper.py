import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse

seenURLs = set()

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page.
    # resp.url: the actual url of the page.
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    extracted_urls =[]
    
    #Checks to make sure status code is 200/OK meaning we got the page
    if resp.status == 200:
        html_content = resp.raw_response.content
    #Returns empty list if we failed to get the page
    else:
        return []

    #If there is content
    if html_content:
        html_parsed = BeautifulSoup(html_content, 'html.parser')
    else:
        #Return early if there is no content, nothing to explore in that URL
        return []

    #Extracts all the URLs found within a page’s <a> tags, based on beautiful soup documentation
    links = html_parsed.find_all('a')
    for link in links:
        #Removes the fragment if there is one before adding to the list of URLs
        toAdd = link.get('href')
        if toAdd is not None:
            frag = toAdd.find('#')
            if frag != -1:
                toAdd = toAdd[0:frag]
            if toAdd not in seenURLs:
                extracted_urls.append(toAdd)
                seenURLs.add(toAdd)

    return extracted_urls

def is_valid(url):
    # Decide whether to crawl these this or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        if re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower()):
            return False
        #Returns false if the url is not within the domains and paths mentioned above
        if ((url.find("ics.uci.edu") != -1) or 
                (url.find("cs.uci.edu") != -1) or 
                (url.find("informatics.uci.edu") != -1) or 
                (url.find("stat.uci.edu") != -1)):
            return True
        return False
    except TypeError:
        print ("TypeError for ", parsed)
        raise
