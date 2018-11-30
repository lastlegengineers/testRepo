from bs4 import BeautifulSoup
import requests, re, sys
#python -m pip install beautifulsoup4
#python -m pip install lxml

def getRange(tag_list, contextref):
    #loop through all tags
    for tag in tag_list:
        #if we hit a context tag, dig deeper
        if tag.name == 'context':
            #if the context tag equals our target refernce return the expected data
            if tag.get('id') == contextref:
                return [tag.startdate.string,tag.enddate.string]


def getCIK(ticker):
    #gets CIK id from stock ticker from SEC
    URL = 'http://www.sec.gov/cgi-bin/browse-edgar?CIK=' + ticker + '&Find=Search&owner=exclude&action=getcompany'
    CIK_RE = re.compile(r'.*CIK=(\d{10}).*')
    f = requests.get(URL, stream = True)
    results = CIK_RE.findall(f.text)
    if len(results):
        results[0] = int(re.sub('\.[0]*', '.', results[0]))
        return str(results[0])

# Access page

cik = getCIK('CVS')
type = '10-'

# Obtain HTML for search page
base_url = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={}&type={}" #&dateb={}"

#print(base_url.format(cik, type)) #, dateb))
edgar_resp = requests.get(base_url.format(cik, type)) #, dateb))
edgar_str = edgar_resp.text

# Find the document link
doc_link = ''
soup = BeautifulSoup(edgar_str, 'html.parser')
table_tag = soup.find('table', class_='tableFile2')
rows = table_tag.find_all('tr')
for row in rows:
    cells = row.find_all('td')
    if len(cells) > 3:
        #if '2015' in cells[3].text:
        print(cells[3].text)
        doc_link = 'https://www.sec.gov' + cells[1].a['href']
        break

# Exit if document link couldn't be found
if doc_link == '':
    print("Couldn't find the document link")
    sys.exit()

# Obtain HTML for document page
doc_resp = requests.get(doc_link)
print(doc_link)
doc_str = doc_resp.text

# Find the XBRL link
rng=[]
xbrl_link = ''
soup = BeautifulSoup(doc_str, 'html.parser')
table_tag = soup.find('table', class_='tableFile', summary='Data Files')
rows = table_tag.find_all('tr')
for row in rows:
    cells = row.find_all('td')
    if len(cells) > 3:
        if 'INS' in cells[3].text:
            xbrl_link = 'https://www.sec.gov' + cells[2].a['href']

# Obtain XBRL text from document
xbrl_resp = requests.get(xbrl_link)
xbrl_str = xbrl_resp.text

# Find and print EPS, EPSd and NetIncome
soup = BeautifulSoup(xbrl_str, 'lxml')
tag_list = soup.find_all()
for tag in tag_list:

    if tag.name == 'us-gaap:earningspersharebasic':
        rng = getRange(tag_list,tag.get('contextref'))
        print("\tEarningsPerShareBasic: ", rng[0], rng[1] , tag.text)

    if tag.name == 'us-gaap:earningspersharediluted':
        rng = getRange(tag_list,tag.get('contextref'))
        print("\tEarningsPerShareDiluted: ", rng[0], rng[1] , tag.text)

    if tag.name == 'us-gaap:netincomeloss' and len(tag.get('contextref')) < 35:
        rng = getRange(tag_list,tag.get('contextref'))
        print("\tNetIncome: ", rng[0], rng[1] , tag.text)


