from mrjob.job import MRJob
from mrjob.step import MRStep
import re
import Queue
import xml.etree.ElementTree as ET

WORD_RE = re.compile(r"[\w']+")


class MRMostUsedWord(MRJob):

    def steps(self):
        self.page = ''
        return [
            MRStep(mapper=self.mapper_get_words,
                   combiner=self.combiner_count_words,
                   reducer=self.reducer_count_words),
            MRStep(reducer=self.reducer_find_max_word)
        ]


    def mapper_get_words(self, _, line):
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
                    for word in WORD_RE.findall(text.text):
                        yield (word.lower(), 1)
            except:
                pass
        else:
            if self.page:
                self.page += line

        

    def combiner_count_words(self, word, counts):
        # optimization: sum the words we've seen so far
        yield (word, sum(counts))

    def reducer_count_words(self, word, counts):
        # send all (num_occurrences, word) pairs to the same reducer.
        # num_occurrences is so we can easily use Python's max() function.
        yield None, (sum(counts), word)

    # discard the key; it is just None
    def reducer_find_max_word(self, _, word_count_pairs):
        # each item of word_count_pairs is (count, word),
        # so yielding one results in key=counts, value=word
        count_word = [i for i in word_count_pairs]
        top100 = sorted(count_word, reverse=True)[0:100]
        print [(a[1], a[0]) for a in top100]
        return 0
        #yield max(word_count_pairs)


if __name__ == '__main__':
    MRMostUsedWord.run()
