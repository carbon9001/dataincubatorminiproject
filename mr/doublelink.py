from mrjob.job import MRJob
from mrjob.step import MRStep
import re
import xml.etree.ElementTree as ET
import mwparserfromhell
import random
import numpy as np
import heapq
import cPickle as cp

WORD_RE = re.compile(r"[\w']+")
head_RE = re.compile(r".*<page>.*")
non_cont_RE = re.compile(r".*:.*?")  


class Doublelink(MRJob):

    def steps(self):
        return [
        MRStep(mapper_init=self.mapper_get_linkstat_init,
        mapper=self.mapper_get_links_mat,
        reducer=self.joinred),
        MRStep(reducer_init=self.sumred_init,
                reducer=self.sumred,
                reducer_final=self.sumred_final),
        MRStep(reducer_init=self.grouped_init,
                   reducer=self.grouped,
                   reducer_final=self.grouped_final)
        ]
    def mapper_get_linkstat_init(self):
        ''' initialization '''
        self.page = ''

    def mapper_get_links_mat(self, _, line):
        ''' find pages, yield number of links on each page; yield page '''
        if line == "  <page>":
            self.page = line
        elif line == "  </page>" and self.page:
            self.page += line
            if not head_RE.match(self.page):
                return
            a = self.page.decode('utf-8','ignore').encode('utf-8','ignore')
            self.page = ''
            root = ET.fromstring(a)

            ''' find the title on each page '''
            wikititle = [x.text for x in root.getiterator() if x.tag=='title']
            title = [item.encode('utf-8', 'ignore').lower() for item in wikititle]
            if len(title) != 1 or non_cont_RE.match(title[0]):
                #print 'non cont title:', title
                return
            #print 'title?:    ', title
            title = title[0]

            ''' find the content links on each page '''
            page_links_num = 0
            page_links = []
            texts = [x.text for x in root.getiterator() if x.tag=='text']
            for text in texts:
                wikicode = mwparserfromhell.parse(text)
                wikilink = wikicode.filter_wikilinks()
                links = [item.encode('utf-8','ignore').lower() for item in wikilink] 
                cont_links = list(set([re.sub('\[\[|\]\]','', item) for item in links if not non_cont_RE.match(item)]))
                #non_cont_links = set([link for link in links if non_cont_RE.match(link)])
                #print '\n',sorted(list(non_cont_links)),'\n'
                #print '\n',sorted(list(cont_links)),'\n'
                page_links_num += len(cont_links)
                page_links.extend(cont_links)

                link_weight = 1./(page_links_num+10.)
                row = [(link, link_weight) for link in page_links]
                #print 'row:',(title, (row,))
                yield (title, (row,)) #(row, (rowvalues, ))
                for link in page_links:
                #	print 'col:',(link, (title, link_weight)) 
                    yield (link, (title, link_weight)) #(col, (row, val))
        else:
            if self.page:
                self.page += line

    def joinred(self, key, vals):
        M2row = []
        M1col = []
        '''
        try:
            print 'key', key 
            print 'vals', vals 
        except: pass
        '''
        for val in vals:
            if len(val) == 1:
            #print 'val', val
                M2row.extend(val[0])
            else:
                M1col.append(val)
                #print 'M2row:',M2row 
                #print 'M1col:',M1col
        for (M2col,M2val) in M2row:
            for (M1row,M1val) in M1col:
                #print (tuple(sorted(set((M1row,M2col)))), M1val*M2val)
                key = sorted(list(set([M1row,M2col])))
                #print key
                if len(key) > 1:
                    yield (key, M1val*M2val)

        '''
        reduce, get elements of MM+(MM)^T
        pick top 100 on each reducer
        '''
    def sumred_init(self):
        self.heap = []

    def sumred(self, key, vals):
        '''
        try:
            print 'key', key 
            print 'vals', vals 
        except: pass
        '''
        pair = (sum(vals), key)
        #print pair
        if len(key) > 1:
            heapq.heappush(self.heap, pair)

    def sumred_final(self):
        for pair in heapq.nlargest(100, self.heap):
            yield None, pair

        '''
        reduce, pick top 100 
        '''
    def grouped_init(self):
        self.heap = []

    def grouped(self, _, vals):
        for val in vals:
            heapq.heappush(self.heap, val)

    def grouped_final(self):
        
        #f= file('resulttest','wb')
        #cp.dump(self.heap,f)
        #f.close()
        top100 = heapq.nlargest(100, self.heap)
        #print top100
        print [(tuple(item[1]), item[0]) for item  in top100]
            
if __name__ == '__main__':
    Doublelink.run()
