from mrjob.job import MRJob
from mrjob.step import MRStep
import xml.etree.ElementTree as ET
import mwparserfromhell
import re
import math

Wordre = re.compile(r"\w+")
ngram = 3


class WordCountwiki_entropy(MRJob):
    
    def find_ngrams(input_list, n):
        return zip(*[input_list[i:] for i in range(n)])

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
                    wikicode = mwparserfromhell.parse(text.text)
                    #textwiki = wikicode.strip_code()
                    #textlower = [word.lower() for word in textwiki]
                    #text_ngrams = find_ngrams(textlower,ngram)
                    #for tempkey in text_ngrams:
                        #yield (tempkey,1)
                    wikitext = " ".join(" ".join(fragment.value.split()) for fragment in wikicode.filter_text())
                    #wikitext = Wordre.findall(wikitext2)
                    #wikitext = wikitext2.split()
                    #for word in wikitext:
                        #yield (word,1)
                    for i in xrange(len(wikitext)-ngram+1):
                        if ngram == 1:
                            tempkey = wikitext[i]
                        elif ngram == 2:
                            tempkey = wikitext[i]+wikitext[i+1]
                        elif ngram == 3:
                            tempkey = wikitext[i]+wikitext[i+1]+wikitext[i+2]
                        yield (tempkey, 1)
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
                MRStep(reducer = self.reducer_calculateintropy)]
    
    def reducer_calculateintropy(self,_,wordcount_pair):
        countword = [i[0] for i in wordcount_pair]
        sumcount = sum(countword)
        entropy = math.log(float(sumcount),2) - 1/float(sumcount)*sum([i * math.log(float(i),2) for i in countword])
        print entropy/ngram
        return 0
        
        
if __name__ == '__main__':
    WordCountwiki_entropy.run()