import requests
from shared.utils import get_date_or_none_from_string
from common.mc import MoneyControl

SEARCH_URL = "https://www.moneycontrol.com/stocks/cptmarket/compsearchnew.php?search_data=&cid=&mbsearch_str=&topsearch_type=1&search_str="
PREFIX_URL = "https://www.moneycontrol.com"


class MoneyControlNews(MoneyControl):

    def __init__(self, exchange, ticker):
        super().__init__(exchange, ticker)


    def fetch_ticker_news(self):
        if not self.soup:
            self.fetch_tiker_page()
        if not self.soup:
            print(f'failed to retrieve page')
            return
        ret = list()
        try:
            news_section = self.soup.find("div", {"id": "news"})
            #print(f'news_section {news_section}')
            anchors = news_section.findChildren(['a'])
            #print(f'anchors {anchors}')
            for anchor in anchors:
                #print(f'anchor {anchor}')
                #print(f"link: {anchor['href']} text: {anchor.text}")
                if anchor.text and anchor.text != '':
                    #print(anchor.parent)
                    spans = anchor.parent.findChildren(['span'])
                    for span in spans:
                        #print(f"{span.text}: {anchor['href']} text: {anchor.text}")
                        n = dict()
                        #'Nov 03 2020
                        n['date'] = get_date_or_none_from_string(span.text[0:11], format='%b %d %Y')
                        n['link'] = anchor['href']
                        n['text'] = anchor.text
                        ret.append(n)
            return ret
            #print(self.soup)
            #self.more_anno_link = PREFIX_URL + str(self.soup.find("div", attrs={"class":"PT5 gL_11", "align":"right"}).find("a")["href"] ) # class name extracted after looking at the document
            #self.more_news_link = PREFIX_URL + str(self.soup.find("div", attrs={"class":"PT5 gL_11 FR"}).find("a")["href"])

        except requests.ConnectionError as ce:
            print("There is a network problem (DNS Failure, refused connectionn etc.). Error : "+str(ce))
            raise Exception
        
        except requests.Timeout as te:
            print("Request timed out. Error : "+str(te))
            raise Exception
        
        except requests.TooManyRedirects as tmre:
            print("The request exceeded the maximum no. of redirections. Error : "+str(tmre))
            raise Exception
        
        except requests.exceptions.RequestException as oe:
            print("Any type of request related error : "+str(oe))
            raise Exception
