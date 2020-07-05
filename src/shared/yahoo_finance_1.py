from lxml import html
import requests
import json
import argparse
from collections import OrderedDict

class YahooFinance1(Exchange):
    def __init__(self, stock):
        self.name = 'Nse'
        self.stock = stock
    
    def get_historical_value(self, start, end):

    def get_headers():
        return {"accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en-GB,en;q=0.9,en-US;q=0.8,ml;q=0.7",
            "cache-control": "max-age=0",
            "dnt": "1",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.122 Safari/537.36"}


    def parse(ticker):
        url = "http://finance.yahoo.com/quote/%s?p=%s" % (ticker, ticker)
        response = requests.get(
            url, verify=False, headers=get_headers(), timeout=30)
        print("Parsing %s" % (url))
        parser = html.fromstring(response.text)
        summary_table = parser.xpath(
            '//div[contains(@data-test,"summary-table")]//tr')
        summary_data = OrderedDict()
        other_details_json_link = "https://query2.finance.yahoo.com/v10/finance/quoteSummary/{0}?formatted=true&lang=en-US&region=US&modules=summaryProfile%2CfinancialData%2CrecommendationTrend%2CupgradeDowngradeHistory%2Cearnings%2CdefaultKeyStatistics%2CcalendarEvents&corsDomain=finance.yahoo.com".format(
            ticker)
        summary_json_response = requests.get(other_details_json_link)
        try:
            json_loaded_summary = json.loads(summary_json_response.text)
            summary = json_loaded_summary["quoteSummary"]["result"][0]
            y_Target_Est = summary["financialData"]["targetMeanPrice"]['raw']
            earnings_list = summary["calendarEvents"]['earnings']
            eps = summary["defaultKeyStatistics"]["trailingEps"]['raw']
            datelist = []

            for i in earnings_list['earningsDate']:
                datelist.append(i['fmt'])
            earnings_date = ' to '.join(datelist)

            for table_data in summary_table:
                raw_table_key = table_data.xpath(
                    './/td[1]//text()')
                raw_table_value = table_data.xpath(
                    './/td[2]//text()')
                table_key = ''.join(raw_table_key).strip()
                table_value = ''.join(raw_table_value).strip()
                summary_data.update({table_key: table_value})
            summary_data.update({'1y Target Est': y_Target_Est, 'EPS (TTM)': eps,
                                'Earnings Date': earnings_date, 'ticker': ticker,
                                'url': url})
            return summary_data
        except ValueError:
            print("Failed to parse json response")
            return {"error": "Failed to parse json response"}
        except:
            return {"error": "Unhandled Error"}


if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument('ticker', help='')
    args = argparser.parse_args()
    ticker = args.ticker
    print("Fetching data for %s" % (ticker))
    scraped_data = parse(ticker)
    print("Writing data to output file")
    with open('%s-summary.json' % (ticker), 'w') as fp:
        json.dump(scraped_data, fp, indent=4)
