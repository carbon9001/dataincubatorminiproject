from mrjob.job import MRJob
from mrjob.step import MRStep
import xml.etree.ElementTree as ET
import mwparserfromhell
import re
import math

Wordre = re.compile(r"\w+")
head_RE = re.compile(r".*<page>.*")
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
                if not head_RE.match(self.page):
                    return
                    #a = unicode(self.page, errors='ignore')
                a = self.page.decode('utf-8','ignore').encode('utf-8','ignore')
                root = ET.fromstring(a)
                self.page = ''
                num_links = 0
                texts = [x.text for x in root.getiterator() if x.tag=='text']
                for text in texts:
                #for text in root.iter('text'):
                    #wikicode = mwparserfromhell.parse(text.text)
                    wikicode = mwparserfromhell.parse(text)
                    #textwiki = str(wikicode.strip_code())
                    #textlower = [word for word in textwiki]
                    #text_ngrams = find_ngrams(textlower,ngram)
                    #for tempkey in text_ngrams:
                        #yield (tempkey,1)
                    textwiki = " ".join(" ".join(fragment.value.split()) for fragment in wikicode.filter_text())
                    for i in xrange(len(textwiki)-ngram+1):
                        if ngram == 1:
                            tempkey = textwiki[i]
                        elif ngram == 2:
                            tempkey = textwiki[i]+textwiki[i+1]
                        elif ngram == 3:
                            tempkey = textwiki[i]+textwiki[i+1]+textwiki[i+2]
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