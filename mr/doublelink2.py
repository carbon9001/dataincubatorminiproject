from mrjob.job import MRJob
from mrjob.step import MRStep
import re
import xml.etree.ElementTree as ET
import mwparserfromhell
import random
import numpy as np
import heapq
import cPickle as cp
import itertools

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
                yield title, (page_links,link_weight)
                for link in page_links:
                    #yield title, (link,link_weight)
                    yield link, (title,link_weight) #(col, (row, val))
                    
            '''
            print 'title: ', title
            print 'page link num:', page_links_num
            print link_weight
            print 'page_links:',len(page_links),  page_links
            '''
        else:
            if self.page:
                self.page += line

    def joinred(self, key, vals):
        tempdic = dict()
        #for val in vals:
            #linklist = val[0]
            #if val[0] in tempdic.keys():
                #tempdic[val[0]] += val[1]
            #else:
                #tempdic[val[0]] = val[1]
        for val in vals:
            linklist = val[0]
            if type(linklist) is list:
                for ll in linklist:
                    if ll in tempdic.keys():
                        tempdic[ll] += val[1]
                    else:
                        tempdic[ll] = val[1]
            else:
                if linklist in tempdic.keys():
                    tempdic[linklist] += val[1]
                else:
                    tempdic[linklist] = val[1]
        templist = list()
        for key,value in tempdic.iteritems():
            templist.append((key,value))
        #import itertools
        templist2 = list(itertools.combinations(templist,2))
        #templist2 = list()
        #for i in xrange(len(templist)-1):
            #templist2.append((templist[i],templist[i+1]))
        for t in templist2:
            k = [t[0][0],t[1][0]]
            v = t[0][1]*t[1][1]
            k = tuple(sorted(k))
            if len(k)>1:
                yield (k, v)
        
        
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
        
        #f= open('result1','wb')
        #cp.dump(heapq,f)
        #f.close()
        top100 = heapq.nlargest(100, self.heap)
        #print top100
        print [(tuple(item[1]), item[0]) for item  in top100]
            
if __name__ == '__main__':
    Doublelink.run()
