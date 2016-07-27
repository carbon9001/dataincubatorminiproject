from mrjob.job import MRJob
from mrjob.step import MRStep
import xml.etree.ElementTree as ET
import mwparserfromhell
import re
import numpy as np

Wordre = re.compile(r"\w+")
head_RE = re.compile(r".*<page>.*")
ngram = 1


class Link_State_simple(MRJob):
    
    def mapper(self,_,line):
        if line == "  <page>":
            self.page = line
        elif line == "  </page>":
            self.page += line
            if not head_RE.match(self.page):
                return
            a = self.page.decode('utf-8','ignore').encode('utf-8','ignore')
            self.page = ''
            num_links = 0
               
            #a = self.page.decode('utf-8','ignore').encode('utf-8','ignore')
            root = ET.fromstring(a)
            for text in root.iter('text'):
                try:
                    wikicode = mwparserfromhell.parse(text.text)
                except:
                    return
                wikilink = wikicode.filter_wikilinks()
                links = set([item.encode('utf-8') for item in wikilink])
                num_links += len(links)
                yield ('num_links', num_links)
                yield ('num_pages', 1)
                
                    
        else:
            if self.page:
                self.page += line
                
                
    def reducer(self,key,value):
        if key == 'num_pages':
            yield ('count', sum(value))
        if key == 'num_links':
            a = np.array([count for count in value])
            yield ('mean', np.mean(a))
            yield ('stdev', np.std(a))
            yield ('25%', np.percentile(a,25))
            yield ('median', np.median(a))
            yield ('75%', np.percentile(a,75))
            
    
    def steps(self):
        self.page = ''
        return [MRStep(mapper = self.mapper,  reducer = self.reducer)]
    
        
        
if __name__ == '__main__':
    Link_State_simple.run()