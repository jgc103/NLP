import math, collections

from nltk import bigrams


class LaplaceBigramLanguageModel:

  def __init__(self, corpus):
    """Initialize your data structures in the constructor."""
    self.unigramCounts = collections.defaultdict(lambda: 0)
    self.bigramCounts = collections.defaultdict(lambda:0)
    self.v = 0
    self.train(corpus)

  def train(self, corpus):
    """ Takes a corpus and trains your language model. 
        Compute any counts or other corpus sttistics in this function.
    """
    for sentence in corpus.corpus:
      previous_word = None
      for datum in sentence.data:
        token = datum.word
        if token != '<s>' or token != '</s>':
          self.unigramCounts[token] += 1
        if previous_word is not None:
          self.bigramCounts[(previous_word,token)]+= 1
        previous_word = token
    self.v = len(self.unigramCounts)

  def score(self, sentence):
    """ Takes a list of strings as argument and returns the log-probability of the 
        sentence using your language model. Use whatever data you computed in train() here.
    """
    score = 0.0
    previous_word = None
    for token in sentence:
      if previous_word is not None:
        count_uni = self.unigramCounts[previous_word] + self.v
        count_b = self.bigramCounts[(previous_word, token)] + 1
        prob = count_b / count_uni
        score += math.log(prob)
      previous_word = token
    return score
