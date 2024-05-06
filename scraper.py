import re
import pickle
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin, urldefrag
import hashlib

#Data structures used to keep track of statistics
seenURLs = set()
crawledURLs = set()
seenSimHash_values= set()
seenSimHashedUrls = set()
seenHashes = set() //checksum
words = {}
alphaNum = ["a","b","c","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z","0","1","2","3","4","5","6","7","8","9"]
maxSize = [-1, '']
stopWords = ['a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', "aren't", 'as', 'at', 'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by', "can't", 'cannot', 'could', "couldn't", 'did', "didn't", 'do', 'does', "doesn't", 'doing', "don't", 'down', 'during', 'each', 'few', 'for', 'from', 'further', 'had', "hadn't", 'has', "hasn't", 'have', "haven't", 'having', 'he', "he'd", "he'll", "he's", 'her', 'here', "here's", 'hers', 'herself', 'him', 'himself', 'his', 'how', "how's", 'i', "i'd", "i'll", "i'm", "i've", 'if', 'in', 'into', 'is', "isn't", 'it', "it's", 'its', 'itself', "let's", 'me', 'more', 'most', "mustn't", 'my', 'myself', 'no', 'nor', 'not', 'of', 'off', 'on', 'once', 'only', 'or', 'other', 'ought', 'our', 'ours\tourselves', 'out', 'over', 'own', 'same', "shan't", 'she', "she'd", "she'll", "she's", 'should', "shouldn't", 'so', 'some', 'such', 'than', 'that', "that's", 'the', 'their', 'theirs', 'them', 'themselves', 'then', 'there', "there's", 'these', 'they', "they'd", "they'll", "they're", "they've", 'this', 'those', 'through', 'to', 'too', 'under', 'until', 'up', 'very', 'was', "wasn't", 'we', "we'd", "we'll", "we're", "we've", 'were', "weren't", 'what', "what's", 'when', "when's", 'where', "where's", 'which', 'while', 'who', "who's", 'whom', 'why', "why's", 'with', "won't", 'would', "wouldn't", 'you', "you'd", "you'll", "you're", "you've", 'your', 'yours', 'yourself', 'yourselves']
startSeeds = ["https://www.ics.uci.edu","https://www.cs.uci.edu","https://www.informatics.uci.edu","https://www.stat.uci.edu"]

#Get a 64 bit hash for the passed in list of tokens
def token_hash(tokens):
    hashedToks = []
    for token in tokens:
        hashVal = hashlib.md5(token.encode('utf-8')).digest()
        #Get only 64 bits of the hash as per prof reccomendation
        hashedToks.append(hashVal[:8])
    return hashedToks

#First generates hashes of tokens, then count the number of 1's and 0's in each column of each token hash, with 0's weighed -1, and 1's 1.
#Final count if positive makes the bit in the final hash at that position 1, else makes it 0
def makeSimhash(tokens):
    hashes = token_hash(tokens)
    finHash = 0
    #For each column, count zeroes and ones and use the sum value to decide on the corresponding bit for
    #hash of the page
    for x in range(0, 64):
        count = 0
        for hashVal in hashes:
            #Have to reverse the binary string we get here because we are reading it left to right
            #but trying to construct it right to left
            hashBin = bin(int.from_bytes(hashVal, 'little')).replace("0b","")
            hashBin = hashBin[::-1]
            #Ensure we have a digit at the place in the string if we are checking
            if x<len(hashBin) and hashBin[x] == '1':
                count = count + 1
            else:
                count = count - 1
        if count > 0:
            finHash = finHash + (1<<x)
    #Convert back to bytes since we seem to store hash as bytes by convention?
    return finHash.to_bytes(8, 'little')

#Returns the distance between hashes/number of bits where they are not the same
def distance(hash1, hash2):
    hash1 = int.from_bytes(hash1, 'little')
    hash2 = int.from_bytes(hash2, 'little')
    #Exclusive or, count 1's as they are the different bits
    distance = bin(hash1 ^ hash2).count('1')
    return distance

#Compares URLs based on hash with previous urls, returning a bool determining if they are similar enough based on a threshold similarity value
def detectSimilarUrl(url) ->bool:
    global seenSimHashedUrls
    tokens, size = tokenize(url)
    simhash_url = makeSimhash(tokens)
    if any(distance(simhash_url, i) < 5 for i in seenSimHashedUrls):
        return True
    seenSimHashedUrls.add(simhash_url)
    pickleSaveSeenSimUrls()
    return False

#Returns hash based on tokens, used to detect exact duplicates
def compute_hash(tokens):
    hash = hashlib.sha256()
    content = ' '.join(tokens)
    hash.update(content.encode('utf-8'))
    return hash.hexdigest()

#Return if list of tokens has been seen before
def exact_duplicate_detection(tokens):
    global seenHashes
    page_hash = compute_hash(tokens)
    if page_hash in seenHashes:
        return True
    seenHashes.add(page_hash)
    pickleSaveSeenHash()
    return False

#Compute simhash of our file using the passed in dictionary and returns a bool indicating if it was similar to previous ones or not
def simhashClose(tokens):
    global seenSimHash_values
    simhash_val = makeSimhash(tokens)
    if any(distance(simhash_val, i) < 5 for i in seenSimHash_values):
        return True
    seenSimHash_values.add(simhash_val)
    pickleSaveSimHash()
    return False

#Given a url, returns how many directories deep it is in it's path 
def directory_length(url) -> int:
    parsed_url=urlparse(url)
    return len(parsed_url.path.split('/')) - 1

#Attempts to load all our global values from their stored pickle files if they exist, otherwise gives them default values.
def pickleLoad() ->None:
    pickleLoadSeenUrls()
    pickleLoadSimHash()
    pickleLoadWords()
    pickleLoadMax()
    pickleLoadCrawledUrls()
    pickleLoadSeenSimUrls()
    pickleLoadSeenHash()
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

#Attempts to load seen url simhash values from pickle file
def pickleLoadSeenSimUrls():
    file = None
    try:
        global seenSimHashedUrls
        file = open("pickleSeenSimUrls", "rb")
        seenSimHashedUrls = pickle.load(file)
    except:
        pass
    finally:
        if file != None:
            file.close()
        return

#Attempts to load seen simhashes for page contents from pickle file
def pickleLoadSeenHash():
    file = None
    try:
        global seenHashes
        file = open("pickleSeenHashes", "rb")
        seenHashes = pickle.load(file)
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

#Attempts to save seem simhash values of urls
def pickleSaveSeenSimUrls() ->None:
    global seenSimHashedUrls
    file = open("pickleSeenSimUrls", "wb")
    pickle.dump(seenSimHashedUrls, file)
    file.close
    return

#Attempts to save seem simhash values of urls
def pickleSaveSeenHash() ->None:
    global seenHashes
    file = open("pickleSeenHashes", "wb")
    pickle.dump(seenHashes, file)
    file.close
    return

#Reads the content and returns a list of the alphanumeric tokens not including stop words within it and total num of tokens including stop words
#I also got rid of single char tokens because most of them were from junk in the file and they weren't really words
def tokenize(content: str) -> (list, int):
    #Vars below are our current token we are building and the list of tokens respectively
    curTok = ''
    tokens = []
    file = None
    cur = 0
    size = 0
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
                if curTok not in stopWords and len(curTok) > 1:
                    tokens.append(curTok)
                if len(curTok) > 1:
                    size = size + 1
                curTok = ''
        cur = cur + 1
    #For when we reach the end of the content, check what our last token is
    #If our curTok isn't empty, add it to token list
    if curTok != '':
        if curTok not in stopWords and len(curTok) > 1:
            tokens.append(curTok)
        if len(curTok) > 1:
            size = size+1
    return tokens, size

def compute_word_frequencies(token_list: list) -> dict:
    """
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
    if len(crawledURLs) == 0:
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
    #Add url to seen
    extracted_urls =[]
    seenURLs.add(url)
    crawledURLs.add(url)
    pickleSaveUrls()
    pickleSaveCrawls()
    #Checks to make sure status code is 200/OK meaning we got the page, or if it's redirected where we extract the redirected link
    redirect_codes = [301, 302, 307, 308]
    if resp == None:
        return []
    html_content = None
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

    #If there is content, parse it else return
    if html_content == None:
        return []
    
    global maxSize
    html_parsed = BeautifulSoup(html_content, "html.parser")
    #Tokenize the string, then update the max_size variables
    tokens, size = tokenize(html_parsed.get_text(' '))
    #Only crawl if there is a reasonable level of content, otherwise don't crawl, done by checking first the number of tokens
    #to make sure they reach a certain threshold
    if len(tokens) < 100:
       return []
    sizes = open("size.txt", "a")
    print(f"Size: {size}, url = {url}, len is {len(tokens)}", file = sizes)
    sizes.close()
    if maxSize[0] == -1 or maxSize[0] < size:
        maxSize[0] = size
        maxSize[1] = url
        pickleSaveMax()
        #Store as longest file in words, but don't crawl through file with more than 60000 tokens as most things with size above this have junk data
        if size>60000:
            return []
    #If file at least roughly 10 mb/10 million characters or more, don't crawl through it, do this here and not earlier though
    #so if it's still the longest file by word count we record that in code above
    if len(html_content)> 10000000:
        return []
    #Check if content is similar using simhash, return empty list without scraping for urls if so
    if url not in startSeeds and (exact_duplicate_detection(tokens) or simhashClose(tokens)):
        rej = open("rejected.txt", "a")
        print(f"simHashClose or exact dup rejected: {url}", file = rej)
        rej.close()
        return []
    # Calculate the given urls' word frequencies
    newFreqs = compute_word_frequencies(tokens)
    #Update global counts
    updateDict(newFreqs)
    #Create a stats.txt if it doesn't exist, otherwise overwrite it, generates statistics of our data
    stats = open("stats.txt", "w")
    print(f"Current token list: {words}", file = stats)
    print(f"Current page with max size is: {maxSize}", file = stats)
    print(f"Seen Urls are: {seenURLs}, and there are {len(seenURLs)}", file = stats)
    print(f"Crawled Urls are: {crawledURLs}, and there are {len(crawledURLs)}", file = stats)
    stats.close()

    #Extracts all the URLs found within a page’s <a> tags, based on beautiful soup documentation
    links = html_parsed.find_all('a')
    for link in links:
        #Removes the fragment if there is one before adding to the list of URLs
        if link.has_attr('href'):
            toAdd = link.get('href')
            toAdd.strip()
            toAdd = urldefrag(toAdd)[0]
            toAdd = urljoin(url, toAdd)
            linkstuff = open("links.txt", "a")
            print(url, toAdd, file=linkstuff)
            extracted_urls.append(toAdd)
    return extracted_urls

def is_valid(url):
    # Decide whether to crawl these this or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        if url in seenURLs:
            return False
        #Check is url is ascii characters
        if not url.isascii():
            return False
        #if directory_length(url)>12:
        #    return False
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        if re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico|webm|flv|pps|ppx"
            + r"|png|tiff?|mid|mp2|mp3|mp4|mpg|img|pptm|potx|ppsx"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower()):
            return False
        #Returns false if the url is not within the domains and paths mentioned above
        seenURLs.add(url)
        pickleSaveUrls()
        #If similar url don't crawl
        if url not in startSeeds and detectSimilarUrl(url):
            rej = open("rejected.txt", "a")
            print(f"detectSimilarURL rejected: {url}", file = rej)
            rej.close()
            return False
        return (((".ics.uci.edu") in (parsed.netloc)) or 
                ((".cs.uci.edu") in (parsed.netloc)) or 
                ((".informatics.uci.edu") in (parsed.netloc)) or 
                ((".stat.uci.edu") in (parsed.netloc)))
    except TypeError:
        print ("TypeError for ", parsed)
        raise
