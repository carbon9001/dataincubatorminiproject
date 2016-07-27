from mrjob.job import MRJob
from mrjob.step import MRStep
import re

WORD_RE = re.compile(r"\w+")

class WordCountMapRed(MRJob):
    def mapper(self,_,line):
        for w in WORD_RE.findall(line):
            yield (w.lower(),1)
    #def combiner(self,word,counts):
        #yield (word,sum(counts))
    def reducer(self,word,counts):
        yield None, (sum(counts),word)
    def steps(self):
        return [
            MRStep(mapper=self.mapper,
                   reducer=self.reducer),
            MRStep(reducer=self.reducer_find_max_word)
        ]
    def reducer_find_max_word(self,_, word_count_pairs):
        # each item of word_count_pairs is (count, word),
        # so yielding one results in key=counts, value=word
        count_word = [i for i in word_count_pairs]
        top100 = sorted(count_word, reverse=True)[0:100]
        print [(a[1], a[0]) for a in top100]
        return 0
        #yield max(word_count_pairs)
    
if __name__ == '__main__':
    WordCountMapRed.run()
    