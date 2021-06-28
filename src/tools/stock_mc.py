#!/usr/bin/env python
import pathlib

EXCEL_PATH = pathlib.Path(__file__).parent.parent.parent.absolute()

def google_moneycontrol_base_sitename(stock_ticker):
    """
    This function will search the base name for the moneycontrol site of the stock_ticker. 
    """
    from googlesearch import search
    import re
    query_string = "moneycontrol fianacial ratio of " + stock_ticker
    ratio_url = ""
    google_search_op_string = search(query_string, num_results=20 )
    for url in google_search_op_string:
        #print(url)
        match = re.match("(.*moneycontrol.*)ratio.*?[/]([0-9A-Z]+)", url)
        if match:
            ratio_url = match.group(1)
            MC_ticker = match.group(2)
            break
    return [ratio_url, MC_ticker]
        

#print(google_moneycontrol_base_sitename("SBIN"))

def pull_ratio_from_moneycontrol(stock_ticker, ratio):
    """
    This function will pull the historical ratios for a stock_ticker
    from the moneycontrol website.
    pulled data:
    1. eps
    2. current ratio
    3. price / book value
    4. dividend payout ratio
    5. net profit margin
    6. EV/EBITDA
    7. debt to equity ratio

    Need: 
    1. D/E 
    2. EPS 
    3. ROCE
    4. ROA
    5. EV
    6. EV/EBITDA
    7. P/BV 
    8. Net Profit Margin  
    9. Book Value
    10. P/E (Calculated from xlsx)

    In moneycontrol the ratios are listed as old and new format. 
    Old Format:
    url https://www.moneycontrol.com/financials/statebankofindia/ratios/SBI#SBI
    ratios: 
    current ratio
    dividend payout ratio net profit
    net profit margin
    ROCE

    New Format:
    url https://www.moneycontrol.com/financials/statebankofindia/ratiosVI/SBI#SBI
    ratios:
    eps
    price / book value
    ROCE
    ROA
    EV
    Book Value
    D/E
    EV/EBITDA
    """
    import requests, re
    from bs4 import BeautifulSoup
    base_url, MC_ticker = google_moneycontrol_base_sitename(stock_ticker)
    # if ratio == "Basic EPS" or ratio == "Price/BV" or ratio == "Return on Capital Employed" or ratio == "Return on Assets" or ratio == "Enterprise Value" or ratio == "Book Value .ExclRevalReserve..Share" or ratio == "Total Debt.Equity" or ratio == "EV.EBITDA" or ratio == "Current Ratio" or ratio == "Dividend Payout Ratio Net Profit" or ratio == "Net Profit Margin":
    ratio_consolidated_url1 = base_url + 'consolidated-ratiosVI/'+MC_ticker+'#'+MC_ticker
    ratio_consolidated_url2 = base_url + 'consolidated-ratiosVI/'+MC_ticker+'/2#'+MC_ticker
    ratio_consolidated_url3 = base_url + 'consolidated-ratiosVI/'+MC_ticker+'/3#'+MC_ticker
    ratio_consolidated_url4 = base_url + 'consolidated-ratiosVI/'+MC_ticker+'/4#'+MC_ticker
    ratio_url1 = base_url + 'ratiosVI/'+MC_ticker+'#'+MC_ticker
    ratio_url2 = base_url + 'ratiosVI/'+MC_ticker+'/2#'+MC_ticker
    ratio_url3 = base_url + 'ratiosVI/'+MC_ticker+'/3#'+MC_ticker
    ratio_url4 = base_url + 'ratiosVI/'+MC_ticker+'/4#'+MC_ticker
    # elif ratio == "Current Ratio" or ratio == "Dividend Payout Ratio Net Profit" or ratio == "Net Profit Margin":
    #     ratio_consolidated_url1 = base_url + 'ratios/'+MC_ticker+'#'+MC_ticker
    #     ratio_consolidated_url2 = base_url + 'ratios/'+MC_ticker+'/2#'+MC_ticker
    #     ratio_consolidated_url3 = base_url + 'ratios/'+MC_ticker+'/3#'+MC_ticker
    #     ratio_consolidated_url4 = base_url + 'ratios/'+MC_ticker+'/4#'+MC_ticker
    #     ratio_url1 = base_url + 'ratios/'+MC_ticker+'#'+MC_ticker
    #     ratio_url2 = base_url + 'ratios/'+MC_ticker+'/2#'+MC_ticker
    #     ratio_url3 = base_url + 'ratios/'+MC_ticker+'/3#'+MC_ticker
    #     ratio_url4 = base_url + 'ratios/'+MC_ticker+'/4#'+MC_ticker
    standalone_ratio = []
    consolidated_ratio = []
    ratio_values = {}
    regex_pattern = "[-]?[0-9]+[,]?[0-9]*?[.]?[0-9]+|[-][-]"
    print("Consolidated " + ratio)
    for url in [ratio_consolidated_url1, ratio_consolidated_url2, ratio_consolidated_url3, ratio_consolidated_url4]:
        page          = requests.get(url)
        soup          = BeautifulSoup(page.text, 'html.parser')
        td_all  = soup.find_all('td')
        ratio_name = ratio
        for td in td_all:
            if td.find(text=re.compile(ratio)):
                ratio_name = td.text.strip()
                year1_ratio = td.find_next('td').text.strip()
                if not re.match(regex_pattern, year1_ratio):
                    break
                else:
                    consolidated_ratio.append(year1_ratio)
                year2_ratio = td.find_next('td').find_next('td').text.strip()
                if not re.match(regex_pattern, year2_ratio):
                    break
                else:
                    consolidated_ratio.append(year2_ratio)
                year3_ratio = td.find_next('td').find_next('td').find_next('td').text.strip()
                if not re.match(regex_pattern, year3_ratio):
                    break
                else:
                    consolidated_ratio.append(year3_ratio)
                year4_ratio = td.find_next('td').find_next('td').find_next('td').find_next('td').text.strip()
                if not re.match(regex_pattern, year4_ratio):
                    break
                else:
                    consolidated_ratio.append(year4_ratio)
                year5_ratio = td.find_next('td').find_next('td').find_next('td').find_next('td').find_next('td').text.strip()
                if not re.match(regex_pattern, year5_ratio):
                    break
                else:
                    consolidated_ratio.append(year5_ratio)
    consolidated_ratio_name = "consolidated " + ratio_name
    ratio_values.update({consolidated_ratio_name:consolidated_ratio})
    print(consolidated_ratio)
    print("Standalone " + ratio)
    for url in [ratio_url1, ratio_url2, ratio_url3, ratio_url4]:
        page          = requests.get(url)
        soup          = BeautifulSoup(page.text, 'html.parser')
        td_all  = soup.find_all('td')
        for td in td_all:
            if td.find(text=re.compile(ratio)):
                ratio_name = td.text.strip()
                year1_ratio = td.find_next('td').text.strip()
                if not re.match(regex_pattern, year1_ratio):
                    break
                else:
                    standalone_ratio.append(year1_ratio)
                year2_ratio = td.find_next('td').find_next('td').text.strip()
                if not re.match(regex_pattern, year2_ratio):
                    break
                else:
                    standalone_ratio.append(year2_ratio)
                year3_ratio = td.find_next('td').find_next('td').find_next('td').text.strip()
                if not re.match(regex_pattern, year3_ratio):
                    break
                else:
                    standalone_ratio.append(year3_ratio)
                year4_ratio = td.find_next('td').find_next('td').find_next('td').find_next('td').text.strip()
                if not re.match(regex_pattern, year4_ratio):
                    break
                else:
                    standalone_ratio.append(year4_ratio)
                year5_ratio = td.find_next('td').find_next('td').find_next('td').find_next('td').find_next('td').text.strip()
                if not re.match(regex_pattern, year5_ratio):
                    break
                else:
                    standalone_ratio.append(year5_ratio)
    print(standalone_ratio)
    standalone_ratio_name = "standalone " + ratio_name
    ratio_values.update({"Standalone "+ratio_name:standalone_ratio})
    #print(len(standalone_ratio))
    return(ratio_values)
                    

    
#pull_ratio_from_moneycontrol('SBI', 'Basic EPS')
#pull_ratio_from_moneycontrol('SBI', 'Current Ratio')
#pull_ratio_from_moneycontrol('SBI', 'Price/BV')
#pull_ratio_from_moneycontrol('SBI', 'Dividend Payout Ratio .NP.')
#pull_ratio_from_moneycontrol('SBI', 'Net Profit Margin')
#pull_ratio_from_moneycontrol('HAL', 'Current Ratio')

def Historical_Performance_of_stock(stock_ticker, excel_path = EXCEL_PATH):
    """
    This function will give the historical performance of a stock with
    max value going to 20 years.
    The Data is collected from the moneycontrol key ratios.
    Covered ratios are :
    1. Basic EPS
    2. Current Ratio
    3. Debt/ Equity Ratio
    4. Dividend Payout Ratio
    
    1. D/E 
    2. EPS 
    3. ROCE
    4. ROA
    5. EV
    6. EV/EBITDA
    7. P/BV 
    8. Net Profit Margin  
    9. Book Value
    10. P/E (Calculated from xlsx)

    Then the details are store in the xls. The XLS is same as the valuation.
    Need to seperate the standalone & consolidated dataframes & print in xlsx.

    """
    from datetime import date
    today                                = date.today()
    current_year                         = today.year
    historical_data                      = {}
    eps_from_moneycontrol                = pull_ratio_from_moneycontrol(stock_ticker, 'Basic EPS')
    current_ratio_from_moneycontrol      = pull_ratio_from_moneycontrol(stock_ticker, 'Current Ratio')
    net_profit_margin_from_moneycontrol  = pull_ratio_from_moneycontrol(stock_ticker, 'Net Profit Margin')
    price_to_book_from_moneycontrol      = pull_ratio_from_moneycontrol(stock_ticker, 'Price/BV')
    dividend_payout_from_moneycontrol    = pull_ratio_from_moneycontrol(stock_ticker, 'Dividend Payout Ratio Net Profit')
    ROCE_from_moneycontrol               = pull_ratio_from_moneycontrol(stock_ticker, 'Return on Capital Employed')
    ROA_from_moneycontrol                = pull_ratio_from_moneycontrol(stock_ticker, 'Return on Assets')
    EV_from_moneycontrol                 = pull_ratio_from_moneycontrol(stock_ticker, 'Enterprise Value')
    BV_from_moneycontrol                 = pull_ratio_from_moneycontrol(stock_ticker, 'Book Value .ExclRevalReserve..Share')
    DE_from_moneycontrol                 = pull_ratio_from_moneycontrol(stock_ticker, 'Total Debt.Equity')
    EVEBITDA_from_moneycontrol           = pull_ratio_from_moneycontrol(stock_ticker, 'EV.EBITDA')
    historical_data.update(eps_from_moneycontrol)
    historical_data.update(current_ratio_from_moneycontrol)
    historical_data.update(net_profit_margin_from_moneycontrol)
    historical_data.update(price_to_book_from_moneycontrol)
    historical_data.update(dividend_payout_from_moneycontrol)
    historical_data.update(ROCE_from_moneycontrol)
    historical_data.update(ROA_from_moneycontrol)
    historical_data.update(EV_from_moneycontrol)
    historical_data.update(BV_from_moneycontrol)
    historical_data.update(DE_from_moneycontrol)
    historical_data.update(EVEBITDA_from_moneycontrol)
    print(historical_data)
    for key in historical_data:
        length = len(historical_data[key])
        if length == 0:
            historical_data[key] = ["--"] * 20
        length = len(historical_data[key])
        if length < 20:
            filler = ["--"] * (20 - length)
            historical_data[key].extend(filler)
    #print(historical_data)
    for key in historical_data:
        historical_data[key] = historical_data[key][0:20]
    print(historical_data)


print(EXCEL_PATH)
#Historical_Performance_of_stock('BDL')
Historical_Performance_of_stock('SBIN')
#Historical_Performance_of_stock('HAL')
#Historical_Performance_of_stock('COCHINSHIP')
