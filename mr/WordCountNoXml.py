from mrjob.job import MRJob
from mrjob.step import MRStep
import xml.etree.ElementTree as ET
import re

Wordre = re.compile(r"\w+")

class WordCountNoXml(MRJob):
    def mapper(self,_,line):
        if line == "  <page>":
            self.page = line
        elif line == "  </page>":
            self.page += line
            try:
                a = unicode(self.page, errors='ignore')
                self.page = ''
                #a = self.page.decode('utf-8','ignore').encode('utf-8','ignore')
                root = ET.fromstring(a)
                for text in root.iter('text'):
                    for word in Wordre.findall(text.text):
                        yield (word.lower(), 1)
            except:
                pass
        else:
            if self.page:
                self.page += line
                
    def combiner(self,word,counts):
        yield (word,sum(counts))
                
    def reducer(self,word,counts):
        yield None, (sum(counts),word)
    
    def steps(self):
        self.page = ''
        return [MRStep(mapper = self.mapper, combiner = self.combiner, reducer = self.reducer),
                MRStep(reducer = self.reducer_find_max_word)]
    
    def reducer_find_max_word(self,_,wordcount_pair):
        countword = [i for i in wordcount_pair]
        top100 = sorted(countword, reverse = True)[:100]
        print [(a[1],a[0]) for a in top100]
        return 0
        
        
if __name__ == '__main__':
    WordCountNoXml.run()