#!/usr/bin/env python
import json
import math
import os
import re
import sys
from collections import defaultdict, Counter
from PorterStemmer import PorterStemmer


class IRSystem:

    def __init__(self):
        # For holding the data - initialized in read_data()
        self.titles = []
        self.docs = []
        self.vocab = []
        # For the text pre-processing.
        self.alphanum = re.compile('[^a-zA-Z0-9]')
        self.p = PorterStemmer()


    def get_uniq_words(self):
        uniq = set()
        for doc in self.docs:
            for word in doc:
                uniq.add(word)
        return uniq


    def __read_raw_data(self, dirname):
        print("Stemming Documents...")

        titles = []
        docs = []
        os.mkdir('%s/stemmed' % dirname)
        title_pattern = re.compile('(.*) \d+\.txt')

        # make sure we're only getting the files we actually want
        filenames = []
        for filename in os.listdir('%s/raw' % dirname):
            if filename.endswith(".txt") and not filename.startswith("."):
                filenames.append(filename)

        for i, filename in enumerate(filenames):
            title = title_pattern.search(filename).group(1)
            print("    Doc %d of %d: %s" % (i+1, len(filenames), title))
            titles.append(title)
            contents = []
            f = open('%s/raw/%s' % (dirname, filename),'r',encoding='Latin-1')
            of = open('%s/stemmed/%s.txt' % (dirname, title),'w',encoding='Latin-1')
            for line in f:
                # make sure everything is lower case
                line = line.lower()
                # split on whitespace
                line = [xx.strip() for xx in line.split()]
                # remove non alphanumeric characters
                line = [self.alphanum.sub('', xx) for xx in line]
                # remove any words that are now empty
                line = [xx for xx in line if xx != '']
                # stem words
                line = [self.p.stem(xx) for xx in line]
                # add to the document's conents
                contents.extend(line)
                if len(line) > 0:
                    of.write(" ".join(line))
                    of.write('\n')
            f.close()
            of.close()
            docs.append(contents)
        return titles, docs


    def __read_stemmed_data(self, dirname):
        print("Already stemmed!")
        titles = []
        docs = []

        # make sure we're only getting the files we actually want
        filenames = []
        for filename in os.listdir('%s/stemmed' % dirname):
            if filename.endswith(".txt") and not filename.startswith("."):
                filenames.append(filename)

        if len(filenames) != 60:
            msg = "There are not 60 documents in ./data/RiderHaggard/stemmed/\n"
            msg += "Remove ./data/RiderHaggard/stemmed/ directory and re-run."
            raise Exception(msg)

        for i, filename in enumerate(filenames):
            title = filename.split('.')[0]
            titles.append(title)
            contents = []
            f = open('%s/stemmed/%s' % (dirname, filename), 'r')
            for line in f:
                # split on whitespace
                line = [xx.strip() for xx in line.split()]
                # add to the document's conents
                contents.extend(line)
            f.close()
            docs.append(contents)

        return titles, docs


    def read_data(self, dirname):
        """
        Given the location of the 'data' directory, reads in the documents to
        be indexed.
        """
        # NOTE: We cache stemmed documents for speed
        #       (i.e. write to files in new 'stemmed/' dir).

        print("Reading in documents...")
        # dict mapping file names to list of "words" (tokens)
        filenames = os.listdir(dirname)
        subdirs = os.listdir(dirname)
        if 'stemmed' in subdirs:
            titles, docs = self.__read_stemmed_data(dirname)
        else:
            titles, docs = self.__read_raw_data(dirname)

        # Sort document alphabetically by title to ensure we have the proper
        # document indices when referring to them.
        ordering = [idx for idx, title in sorted(enumerate(titles),
            key = lambda xx : xx[1])]

        self.titles = []
        self.docs = []
        numdocs = len(docs)
        for d in range(numdocs):
            self.titles.append(titles[ordering[d]])
            self.docs.append(docs[ordering[d]])

        # Get the vocabulary.
        self.vocab = [xx for xx in self.get_uniq_words()]

    def index(self):
        """
        Build an index of the documents.
        """
        print("Indexing...")
        # ------------------------------------------------------------------
        # TODO: Create an inverted index.
        #       Granted this may not be a linked list as in a proper
        #       implementation.

        self.inv_index = defaultdict(lambda:[])
        for doc_id, doc in enumerate(self.docs):
            for word in set(doc):
                self.inv_index[word].append(doc_id)




    def get_posting_unstemmed(self, word):
        """
        Given a word, this *stems* the word and then calls get_posting on the
        stemmed word to get its postings list. You should not change
        this function. 
        """
        word = self.p.stem(word)
        return self.inv_index[word]

    def boolean_retrieve(self, query):
        """
        Given a query in the form of a list of *stemmed* words, this returns
        the list of documents in which *all* of those words occur (ie an AND
        query).
        Return an empty list if the query does not return any documents.
        """
        # ------------------------------------------------------------------
        # TODO: Implement Boolean retrieval. You will want to use your
        #       inverted index that you created in index().
        # Right now this just returns all the possible documents!
        #docs = list(range(len(self.docs)))

        #----------------------------------------

        if not query:
            return []

        query = list(set(query))

        # Intersectar las listas directamente en este método

        result = self.inv_index[query[0]]
        for w in query[1:]:
            doc_list = self.inv_index[w]
            i, j = 0, 0
            temp_result = []
            while i < len(result) and j < len(doc_list):
                if result[i] == doc_list[j]:
                    temp_result.append(result[i])
                    i += 1
                    j += 1
                elif result[i] < doc_list[j]:
                    i += 1
                else:
                    j += 1
            result = temp_result

        return result

    def compute_tfidf(self):
        print("Calculating tf-idf...")
        # -------------------------------------------------------------------
        # TODO: Compute and store TF-IDF values for words and documents.
        #       Recall that you can make use of:
        #         * self.vocab: a list of all distinct (stemmed) words
        #         * self.docs: a list of lists, where the i-th document is
        #                   self.docs[i] => ['word1', 'word2', ..., 'wordN']
        #       NOTE that you probably do *not* want to store a value for every
        #       word-document pair, but rather just for those pairs where a
        #       word actually occurs in the document.

        self.tfidf = defaultdict(float)
        self.document_tf_idf = defaultdict(lambda: defaultdict(float))
        self.document_norms = defaultdict(float)
        total_docs = len(self.docs)

        for doc_id, words in enumerate(self.docs):
            # Contar la frecuencia de cada palabra manualmente
            word_counts = {}
            for word in words:
                if word in word_counts:
                    word_counts[word] += 1
                else:
                    word_counts[word] = 1

            for word, count in word_counts.items():
                tf_value = 1 + math.log10(count)
                doc_freq = len(self.inv_index[word])
                idf_value = math.log10(total_docs / doc_freq) if doc_freq > 0 else 0
                tfidf_value = tf_value * idf_value
                self.tfidf[(word, doc_id)] = tfidf_value
                self.document_tf_idf[doc_id][word] = tfidf_value
                self.document_norms[doc_id] += tfidf_value ** 2


            self.document_norms[doc_id] = math.sqrt(self.document_norms[doc_id])




    def get_tfidf_unstemmed(self, word, document):
        """
        This function gets the TF-IDF of an *unstemmed* word in a document.
        Stems the word and then calls get_tfidf. You should not
        change this interface.
        """
        word = self.p.stem(word)
        return self.tfidf[(word,document)]

    def rank_retrieve(self, query):
        """
        Given a query (a list of words), return a rank-ordered list of
        documents (by ID) and score for the query.
        """
        query_counts = {}
        for term in query:
            if term in query_counts:
                query_counts[term] += 1
            else:
                query_counts[term] = 1

        query_vector = {}
        for term, count in query_counts.items():
            if term in self.vocab:
                query_vector[term] = 1 + math.log10(count)

        scores = defaultdict(float)
        for term, weight in query_vector.items():
            if term not in self.inv_index:
                continue
            for doc_id in self.inv_index[term]:
                term_weight_doc = self.document_tf_idf[doc_id].get(term, 0)
                scores[doc_id] += weight * term_weight_doc

        ranked_results = []
        for doc_id, score in scores.items():
            norm = self.document_norms[doc_id]
            similarity = score / norm if norm > 0 else 0.0
            ranked_results.append((doc_id, similarity))

        ranked_results.sort(key=lambda x: x[1], reverse=True)
        return ranked_results[:10]


    def process_query(self, query_str):
        """
        Given a query string, process it and return the list of lowercase,
        alphanumeric, stemmed words in the string.
        """
        # make sure everything is lower case
        query = query_str.lower()
        # split on whitespace
        query = query.split()
        # remove non alphanumeric characters
        query = [self.alphanum.sub('', xx) for xx in query]
        # stem words
        query = [self.p.stem(xx) for xx in query]
        return query


    def query_retrieve(self, query_str):
        """
        Given a string, process and then return the list of matching documents
        found by boolean_retrieve().
        """
        query = self.process_query(query_str)
        return self.boolean_retrieve(query)


    def query_rank(self, query_str):
        """
        Given a string, process and then return the list of the top matching
        documents, rank-ordered.
        """
        query = self.process_query(query_str)
        return self.rank_retrieve(query)


def run_tests(irsys):
    print("===== Running tests =====")
    ff = open('./data/queries.txt')
    questions = [xx.strip() for xx in ff.readlines()]
    ff.close()
    ff = open('./data/solutions.txt')
    solutions = [xx.strip() for xx in ff.readlines()]
    ff.close()

    epsilon = 1e-4
    for part in range(4):
        points = 0
        num_correct = 0
        num_total = 0

        prob = questions[part]
        soln = json.loads(solutions[part])

        if part == 0:     # inverted index test
            print("Inverted Index Test")
            words = prob.split(", ")
            for i, word in enumerate(words):
                num_total += 1
                posting = irsys.get_posting_unstemmed(word)
                if set(posting) == set(soln[i]):
                    num_correct += 1

        elif part == 1:   # boolean retrieval test
            print("Boolean Retrieval Test")
            queries = prob.split(", ")
            for i, query in enumerate(queries):
                num_total += 1
                guess = irsys.query_retrieve(query)
                if set(guess) == set(soln[i]):
                    num_correct += 1

        elif part == 2:   # tfidf test
            print("TF-IDF Test")
            queries = prob.split("; ")
            queries = [xx.split(", ") for xx in queries]
            queries = [(xx[0], int(xx[1])) for xx in queries]
            for i, (word, doc) in enumerate(queries):
                num_total += 1
                guess = irsys.get_tfidf_unstemmed(word, doc)
                if guess >= float(soln[i]) - epsilon and \
                        guess <= float(soln[i]) + epsilon:
                    num_correct += 1

        elif part == 3:   # cosine similarity test
            print("Cosine Similarity Test")
            queries = prob.split(", ")
            for i, query in enumerate(queries):
                num_total += 1
                ranked = irsys.query_rank(query)
                top_rank = ranked[0]
                if top_rank[0] == soln[i][0]:
                    if top_rank[1] >= float(soln[i][1]) - epsilon and \
                            top_rank[1] <= float(soln[i][1]) + epsilon:
                        num_correct += 1

        feedback = "%d/%d Correct. Accuracy: %f" % \
                (num_correct, num_total, float(num_correct)/num_total)

        print("    Score: %d Feedback: %s" % (num_correct*5, feedback))


if __name__ == '__main__':
    irsys = IRSystem()
    irsys.read_data('./data/RiderHaggard')
    irsys.index()
    irsys.compute_tfidf()
    args = sys.argv[1:]    
    if len(args) == 0:
        run_tests(irsys)
    else:
        query = " ".join(args)
        print("Best matching documents to '%s':" % query)
        results = irsys.query_rank(query)
        for docId, score in results:
            print("%s: %e" % (irsys.titles[docId], score))
