#Import Statements
import scrapy
from urllib.request import urlopen #to open the urls that the dois are put into
import json
import requests
import pprint
import logging

#for the ArticleItem section
from scrapy.item import Item, Field
from scrapy.selector import Selector
from scrapy.spiders import Spider

#for the spiders
from scrapy import Spider
from scrapy.http import TextResponse #defines what response is in xpath

#to run spider in Jupytuer notebook, have to restart the kernel each time to run it
from scrapy.settings import Settings
from scrapy.crawler import CrawlerProcess

#for pipeline
import re

#Running spiders imports
from twisted.internet import reactor
from scrapy.utils.project import get_project_settings
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging

#Defines the items Scrapy is looking for
class ArticleItem(Item):
    title = Field()
    authors = Field()
    doi = Field()
    abstract = Field()
    text = Field()
    figures = Field()

#Pipeline to turn data into JSON file for ACS
#class JsonWriterPipeline(object):
#    def open_spider(self, spider):
#        self.file = open('result.jl', 'w')
        
#    def close_spider(self, spider):
#        self.file.close()

#    def process_item(self, item, spider):
#        line = json.dumps(dict(item)) + "\n"
#        self.file.write(line)
#        return item

#Pipeline for Springer
#class JsonWriterPipelineSpr(object):
#    def open_spider(self, spider):
#        self.file = open(namespr, 'w')

#    def close_spider(self, spider):
#        self.file.close()

#    def process_item(self, item, spider):
#        line = json.dumps(dict(item)) + "\n"
#        self.file.write(line)
#        return item
 
#Defining variable for spiders and pipeline
full_url_acs = ''
full_url_spr = ''
full_url_acs_lst = []
full_url_spr_lst = []
    
#Sort DOIs, under each if statement the corresponding spider for each publisher
dois = open('doi_list.txt')
doi_lst = dois.readlines()
fixed_doi = []
for x in doi_lst:
    fixed_doi.append(re.sub('\n','', x))
doi_lst = fixed_doi

for d in doi_lst:
    test_url = 'http://dx.doi.org/{0}'.format(d)
    
    headers = {'Accept': 'application/citeproc+json'}
    bib_info = json.loads(requests.get(test_url, headers=headers).content)

    if bib_info['publisher'] == 'American Chemical Society (ACS)':
        
        doi_acs = bib_info.get('DOI')
        full_url_acs = 'http://pubs.acs.org/doi/full/{0}'.format(doi_acs)
        response_acs = urlopen(full_url_acs)
        content_acs = response_acs.read()

        full_url_acs_lst.append(full_url_acs)
        
        doiacs_name = re.sub('/', '', doi_acs)
        nameacs = 'doiacs-%s.json' %(doiacs_name)
        
    elif bib_info['publisher'] == 'Springer Nature':
        
        doi_spr = bib_info.get('DOI')
        full_url_spr = 'http://link.springer.com/article/{0}'.format(doi_spr)
        response_spr = urlopen(full_url_spr)
        content_spr = response_spr.read()

        full_url_spr_lst.append(full_url_spr)
        
        doispr_name = re.sub('/', '', doi_spr)
        namespr = 'doispr-%s.json' %(doispr_name)

    else:
        print('wrong publisher')

#Code for Spiders
class ArticleSpider(scrapy.Spider):
    name = 'ArticleSpider'
    allowed_domains = ["http://pubs.acs.org/"]
    start_urls = full_url_acs_lst
    
 #   custom_settings = {
 #       'ITEM_PIPELINES': {'__main__.JsonWriterPipeline': 2,}
 #   }
            
    def parse(self, response):
        item = ArticleItem()
        item['title'] = response.xpath('//span[@class="hlFld-Title"]/text()').extract()
        item['authors'] = response.xpath('//a[@id="authors"]/text()').extract()
        item['doi'] = response.xpath('//div[@id="doi"]/text()').extract()
        item['abstract'] = response.xpath('//p[@class="articleBody_abstractText"]/text()').extract()
        item['text'] = response.xpath('//div[@class="hlFld-Fulltext"]/descendant::text()').extract()
        item['figures'] = response.xpath('//img[@alt="figure"]').extract()
        yield item

class ArticleSpiderSpr(scrapy.Spider):
    name = 'ArticleSpiderSpr'
    allowed_domains = ["https://link.springer.com"]
    start_urls = full_url_spr_lst
            
#    custom_settings = {
#        'ITEM_PIPELINES': {'__main__.JsonWriterPipelineSpr': 1,}
#    }

    def parse(self, response):
        item = ArticleItem()
        item['title'] = response.xpath('//h1[@class="ArticleTitle"]/text()').extract()
        item['authors'] = response.xpath('//span[@class="authors__name"]/text()').extract()
        item['doi'] = response.xpath('//span[@id="doi-url"]/text()').extract()
#        item['abstract'] = response.xpath('//p[@class="SimplePara"]/text()').extract()
        item['text'] = response.xpath('//div[@id="body"]/descendant::text()').extract()
        item['figures'] = response.xpath('//div[@class="MediaObject"]').extract()
        yield item
    
def run():

    settings = get_project_settings()
    settings.set('FEED_FORMAT', 'jsonlines')
    settings.set('FEED_URI', 'result6.jl')

    configure_logging()
    runner = CrawlerRunner(settings)

    runner.crawl(ArticleSpider)
    runner.crawl(ArticleSpiderSpr)

    d = runner.join()
    d.addBoth(lambda _: reactor.stop())

    reactor.run()  # the script will block here until all crawling jobs are finished

if __name__ == '__main__':
    run()

##Opens data scraped into many lists, edits file to concatenate lists
def concatenate_list(input):
    output = ''
    for item in input:
        output = output+item
        return output

result = ''
for line in open('result6.jl', 'r'):
    result = json.loads(line)
    result['text'] = concatenate_list(result['text'])

    print(result['text'])

#    x['text'] = concatenate_list(x['text'])

#


#    resultSpr = json.load(open(namespr, mode='r'))
#    resultSpr['text'] = concatenate_list(resultSpr['text'])

#    fixed_authors = []
#    for x in resultSpr['authors']:
#        fixed_authors.append(re.sub('\xa0', ' ', x))
#    resultSpr['authors'] = fixed_authors
#    with open(namespr, 'w') as jsonFile:
#        json.dump(resultSpr, jsonFile)


#Problems: Not sure how to concatenate lists and add back to file
#Can't run both spiders at the same time
