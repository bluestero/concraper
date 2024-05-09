import os
import re
import csv
import requests
from datetime import datetime
from googlesearch import search
from bs4 import BeautifulSoup as bs


#-Concraper class object-#
class Concraper:

    #-Init function for base objects-#
    def __init__(self, search_limit: int = 10) -> None:

        #-Base objects-#
        self.headers = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246"}
        self.search_limit = search_limit
        self.script_dir = os.path.dirname(os.path.abspath(__file__))

        #-Regex patterns-#
        self.email_pattern = re.compile(r"[a-z0-9#%$*!][a-z0-9.#$!_%+-]+@[a-z0-9.-]+\.[a-z]{2,63}", flags = re.IGNORECASE)
        self.contact_pattern = lambda href, url : re.search(rf"{re.escape(url)}.*(?:contact|reach|support)", href, flags = re.IGNORECASE)
        self.phone_pattern = re.compile(r"^\+?\d{1,4}[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}(?:,\+?\d{1,4}[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9})*$", flags = re.IGNORECASE)


    #-Function for writing a record to the given csv-#
    def write_row(self, filename: str, row: list, mode: str) -> None:

        #-Generating the file name-#
        script_dir = os.getcwd()
        today = datetime.now().strftime("%Y_%m_%d")
        filepath = os.path.join(script_dir, f"{today}_{filename}.csv")

        #-Writing a record-#
        with open(filepath, mode, newline = "", encoding = "utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(row)


    #-Function to fetch result urls from a googled query-#
    def google_it(self, query: str, search_limit: int) -> list:

        #-Searching for the query, storing in a list and returning it-#
        urls = {url for url in search(query, search_limit, "en")}
        print("Found links :", urls)
        return urls


    #-Function to extract urls from a given website-#
    def extract_info(self, url: str, crawl: bool) -> dict:

        #-Base objects-#
        all_emails = set()
        all_phone_numbers = set()

        #-Getting the response and its content
        response = requests.get(url, headers = self.headers)
        soup = bs(response.content, "lxml")

        #-Returning if bad response-#
        if not response.ok:
            self.write_row("failed", [url, response.status_code], "a")

        #-Checking if crawl is true-#
        if crawl:

            #-Finding and formatting all the href tags which contain the required keywords-#
            contact_links = soup.find_all('a', href = lambda href: href and self.contact_pattern(href, url))
            contact_links = {contact["href"] for contact in contact_links}
            print("Contact Links :", contact_links)

            #-Iterating the contact links-#
            for contact in contact_links:
                emails, phone_numbers = self.extract_info(contact, crawl = False)

                #-Adding the extracted contact details to the main object-#
                all_emails.union(emails)
                all_phone_numbers.union(phone_numbers)

        #-Extracting the anchor tags with mailto and tel-#
        emails = soup.find_all('a', href = lambda href: href and ('mailto:' in href))
        phone_numbers = soup.find_all('a', href = lambda href: href and ('tel:' in href))

        #-Extracting the required data from the tags-#
        emails = {email['href'].split(':')[1] for email in emails}
        phone_numbers = {phone["href"] for phone in phone_numbers}

        #-Storing them in the required format in a set-#
        all_emails = all_emails.union(emails)
        all_phone_numbers = all_phone_numbers.union(phone_numbers)

        print(url, all_emails, all_phone_numbers)

        return all_emails, all_phone_numbers


    #-Function to get contact info from searching a query-#
    def get_from_search(self, query: str) -> None:

        #-Creating the result and failed csvs.-#
        self.write_row("result", ["Website", "Phone", "Email"], "w")
        self.write_row("failed", ["Website", "Code"], "w")
        urls = self.google_it(query, self.search_limit)

        #-Iterating the urls-#
        for url in urls:
            emails, phone_numbers = self.extract_info(url, crawl = True)
            self.write_row("result", [url, ", ".join(phone_numbers), ", ".join(emails)], "a")

concraper = Concraper(search_limit = 20)
