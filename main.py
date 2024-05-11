import os
import re
import csv
import requests
from pathlib import Path
from datetime import datetime
from googlesearch import search
from bs4 import BeautifulSoup as bs


#-Custom exception-#
class EmptyInputError(Exception):
    def __init__(self,msg):
        super().__init__(msg)


#-Concraper class object-#
class Concraper:

    #-Init function for base objects-#
    def __init__(self, search_limit: int = 10) -> None:

        #-Base objects-#
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246"}
        self.search_limit = search_limit
        self.script_dir = os.path.dirname(os.path.abspath(__file__))

        #-Regex patterns-#
        self.email_pattern = re.compile(r"[a-z0-9#%$*!][a-z0-9.#$!_%+-]+@[a-z0-9.-]+\.[a-z]{2,63}", flags = re.IGNORECASE)
        self.contact_pattern = lambda href, url : re.search(rf"{re.escape(url)}.*(?:contact|reach|support)", href, flags = re.IGNORECASE)
        self.phone_pattern_loose = re.compile(r"\+?\d{1,4}[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}(?:,\+?\d{1,4}[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9})*", flags = re.IGNORECASE)
        self.phone_pattern_strict = re.compile(r"\+\d{1,4}[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}(?:,\+?\d{1,4}[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9})*", flags = re.IGNORECASE)
        self.twitter_handle_1 = re.compile(r"twitter.com/+@?[a-z0-9_]{1,20}", flags = re.IGNORECASE)
        self.twitter_handle_2 = re.compile(r"twitter.com[^~]{1,50}screen_name=@?[a-z0-9_]{1,20}", flags = re.IGNORECASE)
        self.facebook_id = re.compile(
            r"facebook.com[^~]{1,50}(?:"r"(?:\?|&|profile.php|group.php)"
            r"(?:id=|gid=|ref=name&id=)|[a-z0-9%-]{2,}-|/|__user=|"
            r"\?set=a.(?:[0-9.]+)?)[0-9]{5,}", flags = re.IGNORECASE)
        self.facebook_handle = re.compile(
            r"facebook.com(?:.br|.au)?/+(?:#!/|#1/)?"
            r"(?:pg/|watch/|groups/|events/|\.\.\./|pages/category/(?:photographer|journalist)/|"
            r"home.php[#!\?]{1,3}/|\?[a-z_]{1,}=[a-z_#!?]{1,}/|pages/edit/\?id=\d+#!/|\?_rdr#!/)?"
            r"@?[a-z0-9%.-]{1,50}", flags = re.IGNORECASE)
        self.nstagram_handle = re.compile(
            r"instagram.com(?:.br|.au)?/+(?:accounts/login/\?next=/)"
            r"?[a-z0-9_.]{1,30}", flags = re.IGNORECASE)
        self.linkedin_id = re.compile(
            r"linkedin.com[^~]{1,50}(?:gid=|groupid=|"
            r"gr(?:ou)?ps/|company-beta/|edu/|organization/|edu/school\?id=)"
            r"(?:[a-z0-9&%.~_-]{2,200})?[0-9]{2,10}", flags = re.IGNORECASE)
        self.linkedin_handle = re.compile(
            r"linkedin.com(?:.br|.au)?/+(?:organization-guest/)?"
            r"(?:(?:in/|company/|showcase/|school/|companies/|profile/view\?id=)"
            r"(?:acwaa[a-z0-9_-]{34}|[a-z0-9&%.~_-]{2,200})|"
            r"pub/[a-z0-9&%.~_-]{2,150}/[a-z0-9]{1,3}/[a-z0-9]{1,3}/[a-z0-9]{1,3})", flags = re.IGNORECASE)


    #-Function to fetch result urls from a googled query-#
    def google_it(self, query: str, search_limit: int) -> list:

        #-Searching for the query, storing in a list and returning it-#
        urls = {url for url in search(query, search_limit, "en")}
        return urls


    #-Function for writing a record to the given csv-#
    def write_row(self, filepath: str, row: list, mode: str) -> None:

        #-Writing a record-#
        with open(filepath, mode, newline = "", encoding = "utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(row)


    #-Function to extract contact info from the tag-#
    def extract_from_tag(self, tags: list) -> tuple:

        #-Base objects-#
        all_emails = set()
        all_phone_numbers = set()

        #-Iterating the given list of tags-#
        for tag in tags:

            #-Converting the tag to string text-#
            tag_text = str(tag)

            #-Extracting the contact info using regex patterns and adding them to the main set-#
            all_emails = all_emails.union(set(self.email_pattern.findall(tag_text)))
            all_phone_numbers = all_phone_numbers.union(set(self.phone_pattern_loose.findall(tag_text)))

        #-Returning the extracted contact info-#
        return all_emails, all_phone_numbers


    #-Function to extract urls from a given website-#
    def extract_info(self, url: str, crawl: bool) -> dict:

        #-Base objects-#
        all_emails = set()
        all_phone_numbers = set()

        #-Getting the response and its content using try block-#
        try:
            response = requests.get(url, headers = self.headers, timeout = 30)
            soup = bs(response.content, "lxml")

        #-Returning the error message-#
        except:
            return "Website unreachable."

        #-Returning if bad response-#
        if not response.ok:
            return response.status_code

        #-Checking if crawl is true-#
        if crawl:

            #-Finding and formatting all the href tags which contain the required keywords-#
            contact_links = soup.find_all("a", href = lambda href: href and self.contact_pattern(href, url))
            contact_links = {contact["href"] for contact in contact_links}

            #-Iterating the contact links-#
            for contact in contact_links:
                emails, phone_numbers = self.extract_info(contact, crawl = False)

                #-Adding the extracted contact details to the main object-#
                all_emails.union(emails)
                all_phone_numbers.union(phone_numbers)

        #-Extracting contact info from all the anchors with href-#
        emails, phone_numbers = self.extract_from_tag(soup.find_all('a', href=lambda href: href and ('mailto:' in href or 'tel:' in href)))

        #-Storing them in the required format in a set-#
        all_emails = all_emails.union(emails)
        all_phone_numbers = all_phone_numbers.union(phone_numbers)

        return all_emails, all_phone_numbers


    #-Function for base setup-#
    def base_setup(self, input_file: str = None) -> None:

        #-Start time-#
        self.start_time = datetime.now()
        print(f"Script started at : {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}.")

        #-Creating the filepaths based on the input file-#
        if input_file:
            filename = Path(input_file).stem
            self.result_file = os.path.join(self.script_dir, f"{filename}_result.csv")
            self.failed_file = os.path.join(self.script_dir, f"{filename}_failed.csv")

        #-Else Creating the filepaths based on today's date-#
        else:
            today = datetime.now().strftime("%Y_%m_%d")
            self.result_file = os.path.join(self.script_dir, f"{today}_result.csv")
            self.failed_file = os.path.join(self.script_dir, f"{today}_failed.csv")

        #-Creating the result and failed csvs.-#
        self.write_row(self.result_file, ["Website", "Phone", "Email"], "w")
        self.write_row(self.failed_file, ["Website", "Code"], "w")


    #-Function to process urls list-#
    def process_urls(self, urls: set) -> None:

        #-Iterating the urls-#
        for index, url in enumerate(urls):

            #-Getting the scraped result-#
            result = self.extract_info(url, crawl = True)

            #-Writing the website and its reponse status code if returns status code-#
            if isinstance(result, int):
                self.write_row(self.failed_file, [url, result], "a")
                continue

            #-Writing the website is unreachable if error message-#
            elif isinstance(result, str):
                self.write_row(self.failed_file, [url, result], "a")
                continue

            #-Extracting and writing the emails and phone numbers if get response-#
            emails, phone_numbers = result

            #-Writing in failed csv if no emails and phone numbers-#
            if not (emails or phone_numbers):
                self.write_row(self.failed_file, [url, "No contact found."], "a")

            #-Else writing in result csv if find contact info-#
            else:
                self.write_row(self.result_file, [url, ",".join(phone_numbers), ",".join(emails)], "a")

            #-Adding a counter for URLs processed-#
            if index > 0 and index % 10 == 0:
                print(f"Processed URLs : {index}.")


    #-Function to cleanup after processing the urls-#
    def cleanup(self) -> None:

        #-Removing the failed csv if no records-#
        if os.path.getsize(self.failed_file) < 15:
            os.remove(self.failed_file)

        #-Removing the results csv if no records-#
        print(os.path.getsize(self.result_file))
        if os.path.getsize(self.result_file) < 22:
            os.remove(self.result_file)        

        #-End time-#
        print(f"Script ended at : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.")
        print(f"Total time taken : {datetime.now() - self.start_time}.")


    #-Function to get contact info from searching a query-#
    def get_from_search(self, query: str) -> None:

        #-Getting the urls from the google search using the given query-#
        urls = self.google_it(query, self.search_limit)

        #-Running the process functions in order-#
        self.base_setup()
        self.process_urls(urls)
        self.cleanup()


    #-Function to get contact info from the given input file-#
    def get_from_file(self, input_file: str) -> None:

        #-Empty url set-#
        urls = set()

        #-Opening the given file-#
        with open(input_file, "r") as file:
            for line in file:
                urls.add(line.strip())

        #-Raise exception if empty-#
        if not urls:
            raise EmptyInputError(f"Given input file ({input_file}) contains no urls.")

        #-Running the process functions in order-#
        self.base_setup(input_file)
        self.process_urls(urls)
        self.cleanup()


#-Wrapping the main block-#
if __name__ == "__main__":

    #-Sample test code-#
    concraper = Concraper(search_limit = 10)
    # text = concraper.get_from_search("best company india.")
    text = concraper.get_from_file("list.txt")
