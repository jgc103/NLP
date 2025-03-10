import math, collections

class KneserNeyLanguageModel:

  def __init__(self, corpus):
    """Initialize data structures."""
    self.unigramCounts = collections.defaultdict(lambda: 0)
    self.unigramCountsComplete = collections.defaultdict(lambda: 0)
    self.bigramCounts = collections.defaultdict(lambda: 0)
    self.continuationCounts = collections.defaultdict(lambda: 0)
    self.predecessorCounts = collections.defaultdict(lambda: 0)
    self.v = 0
    self.n = 0
    self.n_b = 0
    self.d = 2  # Discount factor explicitly set to 2

    self.train(corpus)

  def train(self, corpus):
    """ Takes a corpus and trains your language model. 
        Compute any counts or other corpus statistics in this function.
    """
    word_predecessors = collections.defaultdict(set)
    word_continuations = collections.defaultdict(set)

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
          word_predecessors[token].add(previous_word)
          word_continuations[previous_word].add(token)

        previous_word = token
    self.v = len(self.unigramCounts)
    self.n_b = len(self.bigramCounts)

    for word, predecessors in word_predecessors.items():
      self.predecessorCounts[word] = len(predecessors)

    for word, continuations in word_continuations.items():
      self.continuationCounts[word] = len(continuations)

  def score(self, sentence):
    """ Takes a list of strings as argument and returns the log-probability of the 
        sentence using your language model. Use whatever data you computed in train() here.
    """
    score = 0.0
    previous_word = None

    for token in sentence:
            if previous_word is not None:
                bigram_count = self.bigramCounts[(previous_word, token)]
                discount = max(bigram_count - self.d, 0)
                unigram_complete_count = self.unigramCountsComplete[previous_word]
                
                if unigram_complete_count > 0:
                    lambda_w = (self.d / unigram_complete_count) * len(self.bigramCounts)
                else:
                    lambda_w = 0  # Avoid division by zero
                
                p_continuation = self.continuationCounts[token] / self.n_b if self.n_b > 0 else (1 / (self.n + self.v))
                
                prob = (discount / unigram_complete_count) if unigram_complete_count > 0 else 0
                prob += lambda_w * p_continuation
                
                if prob <= 0:  # Backoff to add-one smoothed unigram probability
                    prob = (self.unigramCounts[token] + 1) / (self.n + self.v)

                score += math.log(prob)
            previous_word = token

    return score