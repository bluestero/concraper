# What is concraper?
- It is a python script which crawls websites to find and extract contact info such as email, phone, facebook, twitter, linkedin, instagram.
- It supports 2 modes of input:
  - **Google query:** Can give an input query and search limit and scrape the searched websites for contact info.
  - **Input file:** Can provide an input file with URLs and scape from them.
- It searches based on priority, if find it from more accurate sources, will skip searching from less accurate ones.
- All the scraped and processed data would then be stored inside 2 CSV Files: result and failed.

# Setting up Dependencies
Run the following command to resolve the python packages dependencies:

```bash
pip install -r requirements.txt
```

# Running the code
A small sample code would be to import the concraper and use any of the following input methods to run it:

## Using google search:

```code
from concraper import Concraper

concraper = Concraper(search_limit = 10)
concraper.get_from_search("best company india.")
```

## Using input file:

**Input.txt**
```bash
http://www.mirantis.com
http://www.hi-group.com
http://www.wyncorp.com.my
http://www.racepointglobal.com
```

**Code:**
```
from concraper import Concraper

concraper = Concraper(search_limit = 10)
text = concraper.get_from_file("Input.txt")
```

That's it! With this, you can scrape websites for their contact information with ease. Happy Scraping!
