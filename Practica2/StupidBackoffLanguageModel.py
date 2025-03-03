import math, collections


class StupidBackoffLanguageModel:

  def __init__(self, corpus):
    """Initialize your data structures in the constructor."""
    self.unigramCounts = collections.defaultdict(lambda: 0)
    self.unigramCountsComplete = collections.defaultdict(lambda: 0)
    self.bigramCounts = collections.defaultdict(lambda: 0)
    self.v = 0
    self.n = 0
    self.train(corpus)


  def train(self, corpus):
    """ Takes a corpus and trains your language model. 
        Compute any counts or other corpus statistics in this function.
    """
    for sentence in corpus.corpus:
      previous_word = None
      for datum in sentence.data:
        token = datum.word
        self.unigramCountsComplete[token] += 1
        if token != '<s>' and token != '</s>':
          self.unigramCounts[token] += 1
          self.n += 1
        if previous_word is not None:
          self.bigramCounts[(previous_word, token)] += 1
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
        if self.bigramCounts[(previous_word, token)] > 0:
          count_uni = self.unigramCountsComplete[previous_word]
          count_b = self.bigramCounts[(previous_word, token)]
          prob = count_b / count_uni
        else:
          count = self.unigramCountsComplete[token] + 1
          prob = (count / (self.n + self.v)) * 0.4

        score += math.log(prob)
      previous_word = token
    return score