import os
import re
import csv
import sys
import requests
from pathlib import Path
from datetime import datetime
from googlesearch import search
from bs4 import BeautifulSoup as bs

#-Custom imports-#
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from url_gen import UrlGeneralizer

#-Custom exception-#
class EmptyInputError(Exception):
    def __init__(self,msg):
        super().__init__(msg)


#-Concraper class object-#
class Concraper:

    #-Init function for base objects-#
    def __init__(self, search_limit: int = 10, validate_result: bool = True) -> None:

        #-Base objects-#
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246"}
        self.gen = UrlGeneralizer(bad_url = "Bad", bad_social = "Bad")
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.validate_result = validate_result
        self.search_limit = search_limit

        #-Regex patterns-#
        self.email_pattern = re.compile(r"[a-z0-9#%$*!][a-z0-9.#$!_%+-]+@[a-z0-9.-]+\.[a-z]{2,63}", flags = re.IGNORECASE)
        self.email_pattern = re.compile(r"[a-z0-9#%$*!][a-z0-9.#$!_%+-]+@[a-z0-9.-]+\.(?!png|jpg|gif|bmp|jpeg)[a-z]{2,63}", flags = re.IGNORECASE)
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
        self.linkedin_id = re.compile(
            r"linkedin.com[^~]{1,50}(?:gid=|groupid=|"
            r"gr(?:ou)?ps/|company-beta/|edu/|organization/|edu/school\?id=)"
            r"(?:[a-z0-9&%.~_-]{2,200})?[0-9]{2,10}", flags = re.IGNORECASE)
        self.linkedin_handle = re.compile(
            r"linkedin.com(?:.br|.au)?/+(?:organization-guest/)?"
            r"(?:(?:in/|company/|showcase/|school/|companies/|profile/view\?id=)"
            r"(?:acwaa[a-z0-9_-]{34}|[a-z0-9&%.~_-]{2,200})|"
            r"pub/[a-z0-9&%.~_-]{2,150}/[a-z0-9]{1,3}/[a-z0-9]{1,3}/[a-z0-9]{1,3})", flags = re.IGNORECASE)
        self.instagram_handle = re.compile(
            r"instagram.com(?:.br|.au)?/+(?:accounts/login/\?next=/)"
            r"?[a-z0-9_.]{1,30}", flags = re.IGNORECASE)

        #-Regex dictionaries-#
        self.mail_phone_patterns = {
            "phone": [self.phone_pattern_loose, self.phone_pattern_strict],
            "email": [self.email_pattern],
        }
        self.global_patterns = {
            "phone": [self.phone_pattern_strict],
            "email": [self.email_pattern],
            "instagram": [self.instagram_handle],
            "facebook": [self.facebook_id, self.facebook_handle],
            "linkedin": [self.linkedin_id, self.linkedin_handle],
            "twitter": [self.twitter_handle_1, self.twitter_handle_2],
        }


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
    def extract_from_tag(self, tags: list, patterns_dict: dict) -> dict:

        #-Base object-#
        all_info = {
            "email": set(),
            "phone": set(),
            "facebook": set(),
            "linkedin": set(),
            "twitter": set(),
            "instagram": set(),
        }

        #-Iterating the given list of tags-#
        for tag in tags:

            #-Converting the tag to string text-#
            tag_text = str(tag)

            #-Iterating the dictionary containing different list of patterns-#
            for column, patterns in patterns_dict.items():

                #-Iterating the pattern list-#
                for pattern in patterns:

                    #-Adding the regex matches in the all_info dict-#
                    all_info[column] = all_info[column].union(set(pattern.findall(tag_text)))

        #-Returning the regexed data-#
        return all_info


    #-Function to extract contact info from the tag-#
    def extract_from_soup(self, soup: bs, patterns_dict: dict) -> dict:

        #-Base objects-#
        soup_text = str(soup)
        all_info = {
            "email": set(),
            "phone": set(),
            "facebook": set(),
            "linkedin": set(),
            "twitter": set(),
            "instagram": set(),
        }

        #-Iterating the dictionary containing different list of patterns-#
        for column, patterns in patterns_dict.items():

            #-Iterating the pattern list-#
            for pattern in patterns:

                #-Adding the regex matches in the all_info dict-#
                all_info[column] = all_info[column].union(set(pattern.findall(soup_text)))

        #-Returning the regexed data-#
        return all_info


    #-Functionn to extract data-#
    def extract_info(self, url: str, crawl: bool) -> dict:

        #-Base object-#
        all_info = {
            "email": set(),
            "phone": set(),
            "facebook": set(),
            "linkedin": set(),
            "twitter": set(),
            "instagram": set(),
        }

        #-Getting the response and its content using try block-#
        try:
            response = requests.get(self.url, headers = self.headers, timeout = 30)
            soup = bs(response.content, "lxml")

        #-Returning the error message-#
        except:
            return "Website unreachable."

        #-Returning if bad response-#
        if not response.ok:
            return response.status_code

        if crawl:

            #-Finding and formatting all the href tags which contain the required keywords-#
            contact_links = soup.find_all("a", href = lambda href: href and self.contact_pattern(href, self.url))
            contact_links = {contact["href"] for contact in contact_links}

            #-Iterating the contact links-#
            for contact in contact_links:

                #-Getting the contact dict from the url-#
                contact_dict = self.extract_info(contact, crawl = False)

                #-Adding the contact info to our existing data-#
                all_info = {key: value.union(contact_dict[key]) for key, value in all_info.items() if key in contact_dict}

        #-Extracting the contact info from all the anchors with mailto and tel-#
        contact_dict = self.extract_from_tag(soup.find_all('a', href = lambda href: href and ('mailto:' in href or 'tel:' in href)), self.mail_phone_patterns)

        #-Adding the contact info to our existing data-#
        all_info = {key: value.union(contact_dict[key]) for key, value in all_info.items() if key in contact_dict}
        print(all_info)

        #-Creating a copy of the global patterns-#
        global_patterns = self.global_patterns.copy()

        #-Removing already found data from mailto and tel anchor tags-#
        [global_patterns.pop(column) for column, value in all_info.items() if value]

        #-Extracting the contact info from all the anchors-#
        contact_dict = self.extract_from_soup(soup, global_patterns)

        #-Adding the contact info to our existing data-#
        all_info = {key: value.union(contact_dict[key]) for key, value in all_info.items() if key in contact_dict}

        #-Returning the extracted data-#
        return all_info


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
        self.write_row(self.result_file, ["website", "phone", "email", "facebook", "twitter", "linkedin", "instagram"], "w")
        self.write_row(self.failed_file, ["website", "code"], "w")


    #-Function to clean up the result dict-#
    def validate_result_dict(self, result: dict) -> dict:

        #-Function to validate emails-#
        def validate_email(emails: set) -> set:

            #-Valid emails set-#
            valid_emails = set()

            #-Iterating the emails set-#
            for email in emails:

                #-Getting the domain of the url and email-#
                url_domain = self.gen.generalize(self.url, keep_path = False)
                email_domain = email.split("@")[-1]

                #-Adding the email to the emails set if domain matches-#
                if url_domain == email_domain:
                    valid_emails.add(email)

            #-Returning the valid emails set-#
            return valid_emails

        #-Function to validate socials-#
        def validate_socials(socials: set) -> set:

            #-Valid socials set-#
            valid_socials = set()

            #-Iterating the socials set-#
            for social in socials:

                #-Generalizing the url-#
                url = self.gen.generalize(social)

                #-Adding the social to valid socials set if valid-#
                if url != "Bad":
                    valid_socials.add(url)

            #-Returning the valid socials set-#
            return valid_socials

        #-Dict to map column names with functions-#
        validate_dict = {
            "email": validate_email,
            "facebook": validate_socials,
            "twitter": validate_socials,
            "linkedin": validate_socials,
            "instagram": validate_socials,
        }

        #-Iterating the column name and values set of the result dict-#
        for column, values in result.items():

            #-Validating and adding the validated values if column is present-#
            if column in validate_dict:
                result[column] = validate_dict[column](values)

        #-Returning the validated dict-#
        return result    


    #-Function to process urls list-#
    def process_urls(self, urls: set) -> None:

        #-Iterating the urls-#
        for index, url in enumerate(urls):

            #-Getting the scraped result-#
            self.url = url
            result = self.extract_info(self.url, crawl = True)

            #-Writing the website and its reponse status code if returns status code-#
            if isinstance(result, int):
                self.write_row(self.failed_file, [self.url, result], "a")
                continue

            #-Writing the website is unreachable if error message-#
            elif isinstance(result, str):
                self.write_row(self.failed_file, [self.url, result], "a")
                continue

            #-Writing in failed csv if no contact info found-#
            if not any(result.values()):
                self.write_row(self.failed_file, [self.url, "No contact found."], "a")

            #-Else writing in result csv if find contact info-#
            else:

                #-Validating the result dict if validate result flag is true-#
                if self.validate_result:
                    result = self.validate_result_dict(result)

                #-Writing the record to the result csv-#
                self.write_row(self.result_file, [self.url, *(",".join(contact) for contact in result.values())], "a")

            #-Adding a counter for URLs processed-#
            if index > 0 and index % 10 == 0:
                print(f"Processed URLs : {index}.")


    #-Function to cleanup after processing the urls-#
    def cleanup(self) -> None:

        #-Removing the failed csv if no records-#
        if os.path.getsize(self.failed_file) < 15:
            os.remove(self.failed_file)

        #-Removing the results csv if no records-#
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
    text = concraper.get_from_file("list2.txt")
