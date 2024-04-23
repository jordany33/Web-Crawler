import re
import pickle
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import hashlib
from simhash import Simhash
seenURLs = set()
crawledURLs = set()
seenSimHash_values= []
seenSimHashedUrls = set()
seenHashes = set()
words = {}
alphaNum = ["a","b","c","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z","0","1","2","3","4","5","6","7","8","9"]
maxSize = [-1, '']
stopWords = ['a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', "aren't", 'as', 'at', 'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by', "can't", 'cannot', 'could', "couldn't", 'did', "didn't", 'do', 'does', "doesn't", 'doing', "don't", 'down', 'during', 'each', 'few', 'for', 'from', 'further', 'had', "hadn't", 'has', "hasn't", 'have', "haven't", 'having', 'he', "he'd", "he'll", "he's", 'her', 'here', "here's", 'hers', 'herself', 'him', 'himself', 'his', 'how', "how's", 'i', "i'd", "i'll", "i'm", "i've", 'if', 'in', 'into', 'is', "isn't", 'it', "it's", 'its', 'itself', "let's", 'me', 'more', 'most', "mustn't", 'my', 'myself', 'no', 'nor', 'not', 'of', 'off', 'on', 'once', 'only', 'or', 'other', 'ought', 'our', 'ours\tourselves', 'out', 'over', 'own', 'same', "shan't", 'she', "she'd", "she'll", "she's", 'should', "shouldn't", 'so', 'some', 'such', 'than', 'that', "that's", 'the', 'their', 'theirs', 'them', 'themselves', 'then', 'there', "there's", 'these', 'they', "they'd", "they'll", "they're", "they've", 'this', 'those', 'through', 'to', 'too', 'under', 'until', 'up', 'very', 'was', "wasn't", 'we', "we'd", "we'll", "we're", "we've", 'were', "weren't", 'what', "what's", 'when', "when's", 'where', "where's", 'which', 'while', 'who', "who's", 'whom', 'why', "why's", 'with', "won't", 'would', "wouldn't", 'you', "you'd", "you'll", "you're", "you've", 'your', 'yours', 'yourself', 'yourselves']
startSeeds = ["https://www.ics.uci.edu","https://www.cs.uci.edu","https://www.informatics.uci.edu","https://www.stat.uci.edu"]
#Compares URLs based on their paths, returning a bool determining if they are similar enough based on a threshold similarity value
def similarUrl(url1: str, url2: str) ->bool:
    #Parse urls
    parsed_url1 = urlparse(url1)
    parsed_url2 = urlparse(url2)
    #If different domain don't worry, or if any path has no characters
    if (parsed_url1.netloc != parsed_url2.netloc):
        return False
    #Get individual sections of path and their depths, if its zero you can return since at least one doesn't have a path
    path1 = parsed_url1.path.split('/')
    path2 = parsed_url2.path.split('/')
    len1 = len(path1)
    len2 = len(path2)
    #Path not even same depth or one has no path, no need to check
    if len1 != len2 or min(len1,len2) == 0:
        return False
    #Same length here, but basically check they have each section of path identical except for last, then last is where we do final check
    for x in range(len1-1):
        if path1[x] != path2[x]:
            return False
    minEndLength = min(len(path1[len1-1]), len(path2[len2-1]))
    #If no last parth in path, can just return here to avoid 0 division
    if minEndLength == 0:
        return False
    maxEndLength = max(len(path1[len1-1]), len(path2[len2-1]))
    #Var to count how many letters they share in the same index at last part of their paths
    simCount = 0
    for x in range(minEndLength):
        if path1[len1-1][x] == path1[len1-1][x]:
            simCount = simCount + 1
    #Return true to indicate similar if similarity proportion higher than threshold, else false
    return ((float(simCount)/float(maxEndLength))> 0.9)

#Returns a simhash value made from the list of tokens
def simHash(tokens) -> 'simHash':
    return

#Compute simhash of our file using the passed in dictionary and returns a bool indicating if it was similar to previous ones or not
def simhashClose(tokens):
    global seenSimHash_values
    simhash_val = Simhash(tokens)
    if any(simhash_val.distance(i) < 3 for i in seenSimHash_values):
        return True
    seenSimHash_values.append(simhash_val)
    pickleSaveSimHash()
    return False

#Attempts to load all our global values from their stored pickle files if they exist, otherwise gives them default values
def pickleLoad() ->None:
    pickleLoadSeenUrls()
    pickleLoadSimHash()
    pickleLoadWords()
    pickleLoadMax()
    pickleLoadCrawledUrls()
    return

#Attempts to load seenurls from pickle file
def pickleLoadSeenUrls():
    file = None
    try:
        global seenURLs
        file = open("pickleSeenUrls", "rb")
        seenURLs = pickle.load(file)
    except:
        pass
    finally:
        if file != None:
            file.close()
        return
#Attempts to load craweldurls from pickle file
def pickleLoadCrawledUrls():
    file = None
    try:
        global crawledURLs
        file = open("pickleCrawledUrls", "rb")
        crawledURLs = pickle.load(file)
    except:
        pass
    finally:
        if file != None:
            file.close()
        return

#Attempts to load simhash list from pickle file
def pickleLoadSimHash():
    file = None
    try:
        global seenSimHash_values
        file = open("pickleSeenSimhash", "rb")
        seenSimHash_values = pickle.load(file)
    except:
        pass
    finally:
        if file != None:
            file.close()
        return

#Attempts to load words from pickle file
def pickleLoadWords():
    file = None
    try:
        global words
        file = open("pickleWords", "rb")
        words = pickle.load(file)
    except:
        pass
    finally:
        if file != None:
            file.close()
        return

#Attempts to load max size from pickle file
def pickleLoadMax():
    file = None
    try:
        global maxSize
        file = open("pickleMax", "rb")
        maxSize = pickle.load(file)
    except:
        pass
    finally:
        if file != None:
            file.close()
        return

#Attempts to save all our words dictionary into their pickle file
def pickleSaveWords() ->None:
    global words
    file = open("pickleWords", "wb")
    pickle.dump(words, file)
    file.close
    return

#Attempts to save all list of seen simhashes into their pickle file
def pickleSaveSimHash() ->None:
    global seenSimHash_values
    file = open("pickleSeenSimhash", "wb")
    pickle.dump(seenSimHash_values, file)
    file.close
    return

#Attempts to save set of seen URLs into their pickle file
def pickleSaveUrls() ->None:
    global seenURLs
    file = open("pickleSeenUrls", "wb")
    pickle.dump(seenURLs, file)
    file.close
    return

#Attempts to save set of seen URLs into their pickle file
def pickleSaveCrawls() ->None:
    global crawledURLs
    file = open("pickleCrawledUrls", "wb")
    pickle.dump(crawledURLs, file)
    file.close
    return

#Attempts to save set pair of max size and corresponding url into their pickle file
def pickleSaveMax() ->None:
    global maxSize
    file = open("pickleMax", "wb")
    pickle.dump(maxSize, file)
    file.close
    return

#Returns absolute path given base url and rel_url
# def getAbsolute(base_url:str, rel_url:str) ->str:
#     #If they're the same just return the base back
#     return urljoin(base_url, rel_url)
#     if base_url == rel_url:
#         return base_url
#     parsed_url = urlparse(base_url)
#     #Adding the / to base to allow us to make valid absolute URLs if the rel_url has no slash in front, 
#     #since normally it gets stripped and urljoin creates incorrect urls
#     if len(base_url)>0 and base_url[-1] != '/' and rel_url.find('/') != 0 and '.' not in parsed_url.path.split('/')[-1]:
#         base_url = base_url + '/'
#     return urljoin(base_url, rel_url)

#Given a url, returns how many directories deep it is in it's path 
def directory_length(url) -> int:
    parsed_url=urlparse(url)
    return len(parsed_url.path.split('/')) - 1

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
                if curTok not in stopWords:
                    tokens.append(curTok)
                curTok = ''
        cur = cur + 1
    #For when we reach the end of the content, check what our last token is
    #If our curTok isn't empty, add it to token list
    if curTok != '':
        if curTok not in stopWords:
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
    pickleSaveWords()

def scraper(url, resp):
    #If our words dict is empty, either we just started fresh or we're continuing off after server crash, so try to get values.
    if len(words) == 0:
        pickleLoad()
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
    seenURLs.add(url)
    pickleSaveUrls()
    if url in crawledURLs:
        return []
    crawledURLs.add(url)
    pickleSaveCrawls()
    #Checks to make sure status code is 200/OK meaning we got the page
    redirect_codes = [301, 302, 307, 308]
    if resp.status == 200:
        html_content = resp.raw_response.content
    elif resp.status in redirect_codes:
        # Check if the 'Location' header is present, which contains the redirect URL
        if 'Location' in resp.headers:
            return [resp.headers['Location']]
        else:
            return []
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
        if len(tokens) < 50:
            return []
        if maxSize[0] == -1 or maxSize[0] < len(tokens):
            maxSize[0] = len(tokens)
            maxSize[1] = url
            pickleSaveMax()
        #Calculate the given urls' word frequencies
        newFreqs = compute_word_frequencies(tokens)
        #Check if content is similar using simhash, return empty list without scraping for urls if so
        if url not in startSeeds and simhashClose(newFreqs):
            rej = open("rejected.txt", "a")
            print(f"simHashClose rejected: {url}", file = rej)
            rej.close()
            return []
        #Update global counts
        updateDict(newFreqs)
        #Create a stats.txt if it doesn't exist, otherwise overwrite it
        stats = open("stats.txt", "w")
        print(f"Current token list: {words}", file = stats)
        print(f"Current page with max size is: {maxSize}", file = stats)
        print(f"Seen Urls are: {seenURLs}, and there are {len(seenURLs)}", file = stats)
        print(f"Crawled Urls are: {crawledURLs}, and there are {len(crawledURLs)}", file = stats)
        stats.close()
    else:
        #Return early if there is no content, nothing to explore in that URL
        return []

    #Extracts all the URLs found within a page’s <a> tags, based on beautiful soup documentation
    links = html_parsed.find_all('a')
    for link in links:
        #Removes the fragment if there is one before adding to the list of URLs
        if link.get('href'):
            toAdd = link.get('href')
            toadd = urljoin(base_url, rel_url)
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
            rej = open("rejected.txt", "a")
            print(f"dirLength rejected: {url}", file = rej)
            rej.close()
            return False
        seenURLs.add(url)
        pickleSaveUrls()
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
