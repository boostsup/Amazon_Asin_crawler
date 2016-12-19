# Amazon\_Asin\_crawler
crawl Amazon items by asin number

## how to use it
### More Asin
if you want to scrape more Asin ,just add it to the Asinfeed file.
### More Proxy
The crawler will get proxy list from list.txt, and send an random proxy to crawler.If failed then another random proxy.
### More User Agent
The same one User Agent send too many requests will be blocked by Amazon.So If you want to scrape more item ,such as thousands in one hour,just add more user agents to ua.txt.

It will send a random user agent to crawler.Once failed then another random User agent

### Database

Before running the crawler , you should have to set up mongodb or other database for it.Saving the data to file is ok but not recommended.

## Final
If the result returns none data or  some other errors ,the crawler will scrape the same url untill the right data.