import re
import pickle
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from simhash import Simhash

seenURLs = set()
seenSimHash_values= []
words = {}
alphaNum = ["a","b","c","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z","0","1","2","3","4","5","6","7","8","9"]
maxSize = [-1, '']
stopWords = ['a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', "aren't", 'as', 'at', 'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by', "can't", 'cannot', 'could', "couldn't", 'did', "didn't", 'do', 'does', "doesn't", 'doing', "don't", 'down', 'during', 'each', 'few', 'for', 'from', 'further', 'had', "hadn't", 'has', "hasn't", 'have', "haven't", 'having', 'he', "he'd", "he'll", "he's", 'her', 'here', "here's", 'hers', 'herself', 'him', 'himself', 'his', 'how', "how's", 'i', "i'd", "i'll", "i'm", "i've", 'if', 'in', 'into', 'is', "isn't", 'it', "it's", 'its', 'itself', "let's", 'me', 'more', 'most', "mustn't", 'my', 'myself', 'no', 'nor', 'not', 'of', 'off', 'on', 'once', 'only', 'or', 'other', 'ought', 'our', 'ours\tourselves', 'out', 'over', 'own', 'same', "shan't", 'she', "she'd", "she'll", "she's", 'should', "shouldn't", 'so', 'some', 'such', 'than', 'that', "that's", 'the', 'their', 'theirs', 'them', 'themselves', 'then', 'there', "there's", 'these', 'they', "they'd", "they'll", "they're", "they've", 'this', 'those', 'through', 'to', 'too', 'under', 'until', 'up', 'very', 'was', "wasn't", 'we', "we'd", "we'll", "we're", "we've", 'were', "weren't", 'what', "what's", 'when', "when's", 'where', "where's", 'which', 'while', 'who', "who's", 'whom', 'why', "why's", 'with', "won't", 'would', "wouldn't", 'you', "you'd", "you'll", "you're", "you've", 'your', 'yours', 'yourself', 'yourselves']

#Compares URLs based on their paths, returning a bool determining if they are similar enough based on a threshold similarity value
def similarUrl(url1: str, url2: str) ->bool:
    #Parse urls
    parsed_url1 = urlparse(url1)
    parsed_url2 = urlparse(url2)
    #If different domain don't worry, or if any path has no characters
    if (parsed_url1.netloc != parsed_url2.netloc):
        return False
    #Get minimum path length, if its zero you can return since one doesn't have a path, and we already accounted for identical urls elsewhere
    len1 = len(parsed_url1.path)
    len2 = len(parsed_url2.path)
    minLength = min(len1, len2)
    #Get max and difference in lengths to calculate proportion of identical characters in same index
    maxLength = max(len1, len2)
    diffLen = abs(len1 - len2)
    if minLength == 0:
        return False
    #Var to count how many letters they share in the same index
    simCount = 0
    #Count letters they shared in the same index
    for x in range(minLength):
        if parsed_url1.path[x] == parsed_url2.path[x]:
            simCount = simCount + 1
    #Return true to indicate similar if similarity proportion higher than threshold
    return ((float(simCount)/float(maxLength))> 0.9)

#Returns a boolean indicating whether or not the information reaches has low information value
#Informational value calculated by proportion of stop words to real words
def isLowVal(freqs: dict)->bool:
    #Counts frequency of stop and total words, then finds proportion of stop words relative to total
    countStop = 0
    countTotal = 0
    for x in freqs.keys():
        countTotal = countTotal + freqs[x]
        if x in stopWords:
            countStop = countStop + freqs[x]
    if countTotal == 0:
        return True
    return ((float(countStop)/float(countTotal))>0.65)

#Compute simhash of our file using the passed in dictionary and returns a bool indicating if it was similar to previous ones or not
def simhashClose(tokens_dict):
    global seenSimHash_values
    simhash_val = Simhash(tokens_dict)
    if len(seenSimHash_values)>1 and any(simhash_val.distance(i) <= 3 for i in seenSimHash_values):
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

#Attempts to save set pair of max size and corresponding url into their pickle file
def pickleSaveMax() ->None:
    global maxSize
    file = open("pickleMax", "wb")
    pickle.dump(maxSize, file)
    file.close
    return

#Returns absolute path given base url and rel_url
def getAbsolute(base_url:str, rel_url:str) ->str:
    orig = base_url
    #If they're the same just return the base back
    if base_url == rel_url:
        return base_url
    parsed_url = urlparse(base_url)
    #Adding the / here to allow us to make valid absolute URLs, since normally it gets stripped and urljoin creates incorrect urls
    if '.' not in parsed_url.path.split('/')[-1]:
        base_url = base_url + '/'
    new_url = urljoin(base_url, rel_url)
    #If its not a new url compared to the base, return back joined original and relative, otherwise return new one 
    if base_url != new_url:
        return new_url
    return urljoin(orig, rel_url)

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
        if len(tokens) < 100:
            return []
        if maxSize[0] == -1 or maxSize[0] < len(tokens):
            maxSize[0] = len(tokens)
            maxSize[1] = url
            pickleSaveMax()
        #Calculate the given urls' word frequencies
        newFreqs = compute_word_frequencies(tokens)
        #Check if low information value, return empty list if so because mostly stop words
        if isLowVal(newFreqs):
            return []
        #Check if content is similar using simhash, return empty list without scraping for urls if so
        if simhashClose(newFreqs):
            return []
        #Update global counts
        updateDict(newFreqs)
        #Create a stats.txt if it doesn't exist, otherwise overwrite it
        stats = open("stats.txt", "w")
        print(f"Current token list: {words}", file = stats)
        print(f"Current page with max size is: {maxSize}", file = stats)
        print(f"Urls are: {seenURLs}", file = stats)
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
            toadd = getAbsolute(url, toAdd)
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
        #If url too similar, may be a pattern that leads to trap
        if len(seenURLs)>=1 and any(similarUrl(url, x) for x in seenURLs):
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
