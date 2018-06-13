import csv
import math
import re
import requests
import sys
from BeautifulSoup import BeautifulSoup
from requests.compat import urljoin

## Retrieve all page links
def _getPageLinks():
    pageLinks = {}
    page = '&page='
    pageSize = '&pageSize='
    size = '180'

    base = _getSoup(totalWineUrl)
    tab = base.find('a', attrs={'id' : 'plp-productfull-tabs'})
    input = tab.find('input')
    available = int(input.get('value'))

    # Calculate number of pages. Rounding up
    pages = available/int(size) + (available % int(size) > 0)
    for i in range(50,75):
        pageLinks[i] = totalWineUrl + pageSize + str(size) + page + str(i)

    print '\nThere are '+ str(available) + ' red wines available to you on ' + str(pages) + ' pages.\n'
    return pageLinks

## Get html content
def _getSoup(url):
    response = requests.get(url, timeout = 10)
    html = response.content
    return BeautifulSoup(html)

## Remove apostrophes and commas
def _removeChars(line):
    line = re.sub("&#039;", '', line)
    line = re.sub(u"(\u2018|\u2019|\u2013|\u2014|\xe2)", "", line)
    return re.sub("[\"\',]", '', line)

## Write header of csv
def _writeCsvHeader():
    with open('wine.csv', 'wb') as file:
            headers = ['WineName', 'Price', 'CountryState', 'Region', 'ProductType', 'VarietalType', 'Description']
            writer = csv.DictWriter(file, delimiter = ',', lineterminator = '\n', fieldnames = headers)
            writer.writeheader()

## Write row to csv
def _writeCsvRow(wineRow):
    with open('wine.csv', 'ab') as file:
            writer = csv.writer(file)
            writer.writerow(wineRow)

#### End helper functions


#### Main
totalWineUrl = 'http://www.totalwine.com/wine/c/c0020?tab=fullcatalog&text=&viewall=true&producttype=red-wine'

productLinks = {}
pageLinks = _getPageLinks()

## Make list of links to products
for page in pageLinks:
    wines = _getSoup(pageLinks[page])
    table = wines.find('ul', attrs={'class' : 'plp-list'})
    for products in table.findAll('h2', attrs = {'class' : 'plp-product-title'}):
        for productTitle in products.findAll('a'):
            productLinks[productTitle] = productTitle.get('href')

_writeCsvHeader()
count = 1

# Collect data from the products
for wine in productLinks:
    wineSoup = _getSoup(productLinks[wine])

    # Get name of wine
    productName = wineSoup.find('h1', attrs = {'class' : 'product-name'})
    if productName is None:
        continue
    wineName = _removeChars(productName.text)
    output = '#' + str(count) + ' ' + wineName + '\n'

    # Get wine details
    wineDetails = wineSoup.find('div', attrs = {'class' : 'wine_details'})
    if wineDetails is None:
        continue
    details = wineDetails.findAll('a')
    countryState = ''
    region = ''
    productType = ''
    varietalType = ''
    for a in details:
        if a.get('class') == 'analyticsCountryState':
            countryState = _removeChars(a.text)
            output += countryState + '\n'
        elif a.get('class') == 'analyticsRegion':
            region = _removeChars(a.text)
            output += region + '\n'
        elif a.get('class') == 'analyticsProductType':
            productType = _removeChars(a.text)
            output += productType + '\n'
        elif a.get('class') == 'analyticsVarietalType':
            varietalType = _removeChars(a.text)
            output += varietalType + '\n'

    # Get price
    priceMid = wineSoup.find('span', attrs = {'class' : 'price-style-mid'})
    if priceMid is None:
        continue
    price = _removeChars(priceMid.text)

    # Get wine description
    rightDesc = wineSoup.find('div', attrs = {'class' : 'right-full-desc'})
    if rightDesc is None:
        continue
    desc = _removeChars(rightDesc.find('p').text) + ' ('
    bottomDesc = wineSoup.find('div', attrs = {'class' : 'bottom-full-desc'})
    if bottomDesc is None:
        continue
    spans = bottomDesc.findAll('span')
    for span in spans:
        desc += re.sub("[.]", ' ', _removeChars(span.text)) + ' '
    desc += ')'
    output += desc + '\n\n'

    wineRow = [wineName, price, countryState, region, productType, varietalType, desc]
    _writeCsvRow(wineRow)

    sys.stdout.write(output)
    sys.stdout.flush()

    output = ''
    count += 1
