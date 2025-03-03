import math, collections


class LaplaceUnigramLanguageModel:

  def __init__(self, corpus):
    """Initialize your data structures in the constructor."""
    # TODO your code here
    self.unigramCounts = collections.defaultdict(lambda: 0)
    self.v = 0
    self.n = 0
    self.train(corpus)

  def train(self, corpus):
    """ Takes a corpus and trains your language model. 
        Compute any counts or other corpus statistics in this function.
    """
    for sentence in corpus.corpus:
      for datum in sentence.data:
        token = datum.word
        if token != '<s>' and token != '</s>':
          self.n += 1
          self.unigramCounts[token] += 1

    self.v = len(self.unigramCounts)


  def score(self, sentence):
    """ Takes a list of strings as argument and returns the log-probability of the 
        sentence using your language model. Use whatever data you computed in train() here.
    """
    score = 1
    for token in sentence:
      count = self.unigramCounts[token] + 1
      prob = count / (self.n + self.v)
      score += math.log(prob)
    return score







