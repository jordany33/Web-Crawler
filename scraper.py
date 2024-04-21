import re
import pickle
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from simhash import Simhash

seenURLs = set()
seenSimHash_values= set()
words = {}
alphaNum = ["a","b","c","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z","0","1","2","3","4","5","6","7","8","9"]
maxSize = [-1, '']

#Attempts to load all our global values from their stored pickle files if they exist, otherwise gives them default values
def pickleLoad() ->None:
    return

#Attempts to save all our global values into their pickle files
def pickleLoad() ->None:
    return

#Given a url, returns how many directories deep it is in it's path 
def directory_length(url) -> int:
    parsed_url=urlparse(url)

    if isinstance(parsed_url.path, bytes):
        path_str = parsed_url.path.decode('utf-8')
    else:
        path_str = parsed_url.path

    return len(path_str.split('/')) - 1

#Reads the content and returns a list of the alphanumeric tokens within it
def tokenize(content: str) -> list:
    #Vars below are our current token we are building and the list of tokens respectively
    curTok = ''
    tokens = []
    file = None
    cur = 0
    #Going through the content string at a time
    while cur < len(content):
        #Read at most 5 chars
        c = content[cur]
        #converts character to lowercase if it is alpha, done since we don't care about capitalization, makes it easier to check given
        #we made our list's alpha characters only lowercase
        c = c.lower()
        #If c is alphanum, concatenate it to our current token, else add the current token to list if not empty string and start on a new token
        if c in alphaNum:
            curTok = curTok + c
        else:
            if curTok != '':
                tokens.append(curTok)
                curTok = ''
        cur = cur + 1
    #For when we reach the end of the content, check what our last token is
    #If our curTok isn't empty, add it to token list
    if curTok != '':
        tokens.append(curTok)
    return tokens

def compute_word_frequencies(token_list: list) -> dict:
    """
    Runtime Complexity: O(M), M is the number of tokens in token_list.
        This runtime is average-case.
        The function iterates through each token in token_list once.
        Dictionary operations are O(1).
        There is constant time per token.

    Counts and returns the number of occurrences of each token in the 
    token list using a dictionary.

    :param tokens: List of tokens 
    :return: dict, mapping each token to the number of occurrences
    """
    frequencies = {}

    for i in token_list:
        if i in frequencies:
            frequencies[i] += 1
        else:
            frequencies[i] = 1

    return frequencies

#Updates our global dictionary words frequency count for tokens using dic2
def updateDict(dic2:dict) -> None:
    global words
    for x in dic2:
        if x in words:
            words[x] += dic2[x]
        else:
            words[x] = dic2[x]

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def simhashing(tokens_dict, seenSimHash_values):
    simhash_page = Simhash(tokens_dict)
    if any(simhash_page.distance(Simhash(i)) <= 3 for i in seenSimHash_values):
        return []
    
    seenSimHash_values.add(simhash_page.value)
    return simhash_page.value

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
    seenURLs.add(url)
    
    #Checks to make sure status code is 200/OK meaning we got the page
    if resp.status == 200:
        html_content = resp.raw_response.content
    #Returns empty list if we failed to get the page
    else:
        return []

    #If there is content, parse it
    if html_content:
        global maxSize
        html_parsed = BeautifulSoup(html_content, 'lxml')
        #Tokenize the string, then update the max_size variables
        tokens = tokenize(html_parsed.get_text())
        #Only crawl if there is a reasonable level of content, otherwise don't crawl, done by checking first the number of tokens
        #to make sure they reach a certain threshold
        if len(tokens) < 250:
            return []
        if maxSize[0] == -1 or maxSize[0] < len(tokens):
            maxSize[0] = len(tokens)
            maxSize[1] = url
        newFreqs = compute_word_frequencies(tokens)
        updateDict(newFreqs)
        #Create a stats.txt if it doesn't exist, otherwise overwrite it
        stats = open("stats.txt", "w")
        print(f"Current token list: {words}", file = stats)
        print(f"Current page with max size is: {maxSize}", file = stats)
    else:
        #Return early if there is no content, nothing to explore in that URL
        return []

    #Extracts all the URLs found within a page’s <a> tags, based on beautiful soup documentation
    links = html_parsed.find_all('a')
    for link in links:
        #Removes the fragment if there is one before adding to the list of URLs
        if link.get('href'):
            toAdd = link.get('href')
            toadd = urljoin(url, toAdd)
            frag = toAdd.find('#')
            if frag != -1:
                toAdd = toAdd[0:frag]
            extracted_urls.append(toAdd)

    return extracted_urls

def is_valid(url):
    # Decide whether to crawl these this or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        if url in seenURLs:
            return False
        #If you go really deep into directories, at a certain threshold you are probably going into a trap
        if directory_length(url) > 10:
            return False
        seenURLs.add(url)
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
        if (((".ics.uci.edu") in (parsed.netloc)) or 
                ((".cs.uci.edu") in (parsed.netloc)) or 
                ((".informatics.uci.edu") in (parsed.netloc)) or 
                ((".stat.uci.edu") in (parsed.netloc))):
            return True
        return False
    except TypeError:
        print ("TypeError for ", parsed)
        raise

