import collections
import copy
import optparse

from ling.Tree import Tree
import ling.Trees as Trees
import pennParser.EnglishPennTreebankParseEvaluator as \
        EnglishPennTreebankParseEvaluator
import io2.PennTreebankReader as PennTreebankReader
import io2.MASCTreebankReader as MASCTreebankReader
from collections import defaultdict

class Parser:

    def train(self, train_trees):
        pass

    def get_best_parse(self, sentence):
        """
        Should return a Tree
        """
        pass


class PCFGParser(Parser):

    def train(self, train_trees):
        train_trees=[TreeBinarization.binarize_tree(tree) for tree in train_trees]    
        self.lexicon = Lexicon(train_trees)
        self.grammar = Grammar(train_trees)

    def get_best_parse(self, sentence):
        length = len(sentence)
        nonterminals = set(self.grammar.unary_rules_by_child.keys()) | \
                       set(self.grammar.binary_rules_by_left_child.keys()) | \
                       set(self.grammar.binary_rules_by_right_child.keys())

        score = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
        back = defaultdict(lambda: defaultdict(dict))

        # Initialization (lexicon rules)
        for i, word in enumerate(sentence):
            for tag in self.lexicon.get_all_tags():
                prob = self.lexicon.score_tagging(word, tag)
                if prob > 0:
                    score[i][i + 1][tag] = prob
                    back[i][i + 1][tag] = word

            # Unary closure
            added = True
            while added:
                added = False
                for unary in self.grammar.get_unary_rules_by_child(tag):
                    prob = unary.score * score[i][i + 1][unary.child]
                    if prob > score[i][i + 1][unary.parent]:
                        score[i][i + 1][unary.parent] = prob
                        back[i][i + 1][unary.parent] = unary

                        added = True

        # CKY parsing
        for span in range(2, length + 1):
            for begin in range(length - span + 1):
                end = begin + span
                for split in range(begin + 1, end):
                    for B in score[begin][split]:
                        for C in score[split][end]:
                            for rule in self.grammar.get_binary_rules_by_left_child(B):
                                if rule.right_child == C:
                                    prob = score[begin][split][B] * score[split][end][C] * rule.score
                                    if prob > score[begin][end][rule.parent]:
                                        score[begin][end][rule.parent] = prob
                                        back[begin][end][rule.parent] = (split, B, C)

                # Unary closure again
                added = True
                while added:
                    added = False
                    for B in score[begin][end]:
                        for rule in self.grammar.get_unary_rules_by_child(B):
                            prob = rule.score * score[begin][end][rule.child]
                            if prob > score[begin][end][rule.parent]:
                                score[begin][end][rule.parent] = prob
                                back[begin][end][rule.parent] = rule
                                added = True

        # Build tree from backpointers
        if "ROOT" not in score[0][length]:
            return Tree("ROOT", [Tree("FAIL")])

        return TreeBinarization.unbinarize_tree(self.build_tree(back, 0, length, "ROOT", sentence))

    def build_tree(self, back, i, j, label, sentence):
        back_entry = back[i][j][label]

        if isinstance(back_entry, str):
            return Tree(label, [Tree(back_entry)])

        elif isinstance(back_entry, UnaryRule):
            child = self.build_tree(back, i, j, back_entry.child, sentence)
            return Tree(label, [child])

        elif isinstance(back_entry, tuple):  # Binary rule
            split, B, C = back_entry
            left = self.build_tree(back, i, split, B, sentence)
            right = self.build_tree(back, split, j, C, sentence)
            return Tree(label, [left, right])


class BaselineParser(Parser):

    def train(self, train_trees):
        self.lexicon = Lexicon(train_trees)
        self.known_parses = {}
        self.span_to_categories = {}
        for train_tree in train_trees:
            tags = train_tree.get_preterminal_yield()
            tags = tuple(tags)  # because lists are not hashable, but tuples are
            if tags not in self.known_parses:
                self.known_parses[tags] = {}
            if train_tree not in self.known_parses[tags]:
                self.known_parses[tags][train_tree] = 1
            else:
                self.known_parses[tags][train_tree] += 1
            self.tally_spans(train_tree, 0)

    def get_best_parse(self, sentence):
        tags = self.get_baseline_tagging(sentence)
        tags = tuple(tags)
        if tags in self.known_parses:
            return self.get_best_known_parse(tags, sentence)
        else:
            return self.build_right_branch_parse(sentence, list(tags))

    def build_right_branch_parse(self, words, tags):
        cur_position = len(words) - 1
        right_branch_tree = self.build_tag_tree(words, tags, cur_position)
        while cur_position > 0:
            cur_position -= 1
            right_branch_tree = self.merge(
                    self.build_tag_tree(words, tags, cur_position),
                    right_branch_tree)
        right_branch_tree = self.add_root(right_branch_tree)
        return right_branch_tree

    def merge(self, left_tree, right_tree):
        span = len(left_tree.get_yield()) + len(right_tree.get_yield())
        maxval = max(self.span_to_categories[span].values())
        for key in self.span_to_categories[span]:
            if self.span_to_categories[span][key] == maxval:
                most_freq_label = key
                break
        return Tree(most_freq_label, [left_tree, right_tree])

    def add_root(self, tree):
        return Tree("ROOT", [tree])

    def build_tag_tree(self, words, tags, cur_position):
        leaf_tree = Tree(words[cur_position])
        tag_tree = Tree(tags[cur_position], [leaf_tree])
        return tag_tree

    def get_best_known_parse(self, tags, sentence):
        maxval = max(self.known_parses[tags].values())
        for key in self.known_parses[tags]:
            if self.known_parses[tags][key] == maxval:
                parse = key
                break
        parse = copy.deepcopy(parse)
        parse.set_words(sentence)
        return parse

    def get_baseline_tagging(self, sentence):
        tags = [self.get_best_tag(word) for word in sentence]
        return tags

    def get_best_tag(self, word):
        best_score = 0
        best_tag = None
        for tag in self.lexicon.get_all_tags():
            score = self.lexicon.score_tagging(word, tag)
            if best_tag is None or score > best_score:
                best_score = score
                best_tag = tag
        return best_tag

    def tally_spans(self, tree, start):
        if tree.is_leaf() or tree.is_preterminal():
            return 1
        end = start
        for child in tree.children:
            child_span = self.tally_spans(child, end)
            end += child_span
        category = tree.label
        if category != "ROOT":
            if end-start not in self.span_to_categories:
                self.span_to_categories[end-start] = {}
            if category not in self.span_to_categories[end-start]:
                self.span_to_categories[end-start][category] = 1
            else:
                self.span_to_categories[end-start][category] += 1
        return end - start


class TreeBinarization:
    
    @classmethod
    def binarize_tree(cls, tree):
        label = tree.label
        if tree.is_leaf():
            return Tree(label)
        if len(tree.children) == 1:
            return Tree(label, [TreeBinarization.binarize_tree(tree.children[0])])

        intermediate_label = "@%s->" % label
        intermediate_tree = TreeBinarization.binarize_tree_helper(
                tree, 0, intermediate_label)
        return Tree(label, intermediate_tree.children)

    @classmethod
    def binarize_tree_helper(cls, tree, num_children_generated,
            intermediate_label):
        left_tree = tree.children[num_children_generated]
        children = []
        children.append(TreeBinarization.binarize_tree(left_tree))
        if num_children_generated < len(tree.children) - 1:
            right_tree = TreeBinarization.binarize_tree_helper(
                    tree, num_children_generated + 1,
                    intermediate_label + "_" + left_tree.label)
            children.append(right_tree)
        return Tree(intermediate_label, children)


    @classmethod
    def at_filter(cls, string):
        if string.startswith('@'):
            return True
        else:
            return False

    @classmethod
    def unbinarize_tree(cls, tree):
        """
        Remove intermediate nodes (labels beginning with "@")
        Example: a node with label @NP->DT_JJ will be spliced out,
        """
        return Trees.splice_nodes(tree, TreeBinarization.at_filter)


class Lexicon:
    """
    Simple default implementation of a lexicon, which scores word,
    tag pairs with a smoothed estimate of P(tag|word)/P(tag).

    Instance variables:
    word_to_tag_counters
    total_tokens
    total_word_types
    tag_counter
    word_counter
    type_tag_counter
    """

    def __init__(self, train_trees):
        """
        Builds a lexicon from the observed tags in a list of training
        trees.
        """
        self.total_tokens = 0.0
        self.total_word_types = 0.0
        self.word_to_tag_counters = collections.defaultdict(lambda: \
                collections.defaultdict(lambda: 0.0))
        self.tag_counter = collections.defaultdict(lambda: 0.0)
        self.word_counter = collections.defaultdict(lambda: 0.0)
        self.type_to_tag_counter = collections.defaultdict(lambda: 0.0)

        for train_tree in train_trees:
            words = train_tree.get_yield()
            tags = train_tree.get_preterminal_yield()
            for word, tag in zip(words, tags):
                self.tally_tagging(word, tag)


    def tally_tagging(self, word, tag):
        if not self.is_known(word):
            self.total_word_types += 1
            self.type_to_tag_counter[tag] += 1
        self.total_tokens += 1
        self.tag_counter[tag] += 1
        self.word_counter[word] += 1
        self.word_to_tag_counters[word][tag] += 1


    def get_all_tags(self):
        return list(self.tag_counter.keys())


    def is_known(self, word):
        return word in self.word_counter


    def score_tagging(self, word, tag):
        p_tag = float(self.tag_counter[tag]) / self.total_tokens
        c_word = float(self.word_counter[word])
        c_tag_and_word = float(self.word_to_tag_counters[word][tag])
        if c_word < 10:
            c_word += 1
            c_tag_and_word += float(self.type_to_tag_counter[tag]) \
                    / self.total_word_types
        p_word = (1.0 + c_word) / (self.total_tokens + self.total_word_types)
        p_tag_given_word = c_tag_and_word / c_word
        return p_tag_given_word / p_tag * p_word


class Grammar:
    """
    Simple implementation of a PCFG grammar, offering the ability to
    look up rules by their child symbols.  Rule probability estimates
    are just relative frequency estimates off of training trees.

    self.binary_rules_by_left_child
    self.binary_rules_by_right_child
    self.unary_rules_by_child
    """

    def __init__(self, train_trees):
        self.unary_rules_by_child = collections.defaultdict(lambda: [])
        self.binary_rules_by_left_child = collections.defaultdict(
                lambda: [])
        self.binary_rules_by_right_child = collections.defaultdict(
                lambda: [])

        unary_rule_counter = collections.defaultdict(lambda: 0)
        binary_rule_counter = collections.defaultdict(lambda: 0)
        symbol_counter = collections.defaultdict(lambda: 0)

        for train_tree in train_trees:
            self.tally_tree(train_tree, symbol_counter,
                    unary_rule_counter, binary_rule_counter)
        for unary_rule in unary_rule_counter:
            unary_prob = float(unary_rule_counter[unary_rule]) \
                    / symbol_counter[unary_rule.parent]
            unary_rule.score = unary_prob
            self.add_unary(unary_rule)
        for binary_rule in binary_rule_counter:
            binary_prob = float(binary_rule_counter[binary_rule]) \
                    / symbol_counter[binary_rule.parent]
            binary_rule.score = binary_prob
            self.add_binary(binary_rule)


    def __unicode__(self):
        rule_strings = []
        for left_child in self.binary_rules_by_left_child:
            for binary_rule in self.get_binary_rules_by_left_child(
                    left_child):
                rule_strings.append(str(binary_rule))
        for child in self.unary_rules_by_child:
            for unary_rule in self.get_unary_rules_by_child(child):
                rule_strings.append(str(unary_rule))
        return "%s\n" % "".join(rule_strings)


    def add_binary(self, binary_rule):
        self.binary_rules_by_left_child[binary_rule.left_child].\
                append(binary_rule)
        self.binary_rules_by_right_child[binary_rule.right_child].\
                append(binary_rule)


    def add_unary(self, unary_rule):
        self.unary_rules_by_child[unary_rule.child].append(unary_rule)


    def get_binary_rules_by_left_child(self, left_child):
        return self.binary_rules_by_left_child[left_child]


    def get_binary_rules_by_right_child(self, right_child):
        return self.binary_rules_by_right_child[right_child]


    def get_unary_rules_by_child(self, child):
        return self.unary_rules_by_child[child]


    def tally_tree(self, tree, symbol_counter, unary_rule_counter,
            binary_rule_counter):
        if tree.is_leaf():
            return
        if tree.is_preterminal():
            return
        if len(tree.children) == 1:
            unary_rule = self.make_unary_rule(tree)
            symbol_counter[tree.label] += 1
            unary_rule_counter[unary_rule] += 1
        if len(tree.children) == 2:
            binary_rule = self.make_binary_rule(tree)
            symbol_counter[tree.label] += 1
            binary_rule_counter[binary_rule] += 1
        if len(tree.children) < 1 or len(tree.children) > 2:
            raise Exception("Attempted to construct a Grammar with " \
                    + "an illegal tree (most likely not binarized): " \
                    + str(tree))
        for child in tree.children:
            self.tally_tree(child, symbol_counter, unary_rule_counter,
                    binary_rule_counter)


    def make_unary_rule(self, tree):
        return UnaryRule(tree.label, tree.children[0].label)


    def make_binary_rule(self, tree):
        return BinaryRule(tree.label, tree.children[0].label,
                tree.children[1].label)


class BinaryRule:
    """
    A binary grammar rule with score representing its probability.
    """

    def __init__(self, parent, left_child, right_child):
        self.parent = parent
        self.left_child = left_child
        self.right_child = right_child
        self.score = 0.0


    def __str__(self):
        return "%s->%s %s %% %s" % (self.parent, self.left_child, self.right_child, self.score)


    def __hash__(self):
        result = hash(self.parent)
        result = 29 * result + hash(self.left_child)
        result = 29 * result + hash(self.right_child)
        return result


    def __eq__(self, o):
        if self is o:
            return True

        if not isinstance(o, BinaryRule):
            return False

        if (self.left_child != o.left_child):
            return False
        if (self.right_child != o.right_child):
            return False
        if (self.parent != o.parent):
            return False
        return True


class UnaryRule:
    """
    A unary grammar rule with score representing its probability.
    """

    def __init__(self, parent, child):
        self.parent = parent
        self.child = child
        self.score = 0.0

    def __str__(self):
        return "%s->%s %% %s" % (self.parent, self.child, self.score)

    def __hash__(self):
        result = hash(self.parent)
        result = 29 * result + hash(self.child)
        return result

    def __eq__(self, o):
        if self is o:
            return True

        if not isinstance(o, UnaryRule):
            return False

        if (self.child != o.child):
            return False
        if (self.parent != o.parent):
            return False
        return True




def test_parser(parser, test_trees, max_length="20"):   
    evaluator = EnglishPennTreebankParseEvaluator.LabeledConstituentEval(
            ["ROOT"], set(["''", "``", ".", ":", ","]))
    for test_tree in test_trees:
        test_sentence = test_tree.get_yield()
        if len(test_sentence) > max_length:
            continue
        guessed_tree = parser.get_best_parse(test_sentence)
        print("Guess:\n%s" % Trees.PennTreeRenderer.render(guessed_tree))
        print("Gold:\n%s" % Trees.PennTreeRenderer.render(test_tree))
        evaluator.evaluate(guessed_tree, test_tree)
    print("")
    return evaluator.display(True)


def read_trees(base_path, low=None, high=None):
    trees = PennTreebankReader.read_trees(base_path, low, high)
    return [Trees.StandardTreeNormalizer.transform_tree(tree) \
        for tree in trees]


def read_masc_trees(base_path, low=None, high=None):
    print("Reading MASC from %s" % base_path)
    trees = MASCTreebankReader.read_trees(base_path, low, high)
    return [Trees.StandardTreeNormalizer.transform_tree(tree) \
        for tree in trees]


if __name__ == '__main__':
    opt_parser = optparse.OptionParser()
    opt_parser.add_option("--data", dest="data", default = "masc") #change default value ("miniTest") to "masc"
    opt_parser.add_option("--parser", dest="parser",default="PCFGParser") # change default value ("BaselineParser") to "PCFGParser"
    opt_parser.add_option("--maxLength", dest="max_length",default="20") 

    (options, args) = opt_parser.parse_args()
    options = vars(options)

    print("PCFGParserTest options:")
    for opt in options:
        print("  %-12s: %s" % (opt, options[opt]))
    print("")
    max_length = int(options['max_length'])

    parser = globals()[options['parser']]()
    print("Using parser: %s" % parser.__class__.__name__)

    data_set = options['data']

    print("Data will be loaded from: ./data/")

    train_trees = []
    test_trees = []

    if data_set == 'miniTest':

        # training data: first 3 of 4 datums
        print("Loading training trees...")
        train_trees = read_trees('./data/parser/miniTest', 1, 3)
        print("done.")

        # test data: last of 4 datums
        print("Loading test trees...")
        test_trees = read_trees('./data/parser/miniTest', 4, 4)
        print("done.")

    if data_set == "masc":

        # training data: MASC train
        print("Loading MASC training trees... from: ./data/parser/masc/train")
        train_trees.extend(read_masc_trees("./data/parser/masc/train", 0, 34))
        print("done.")
        print("Train trees size: %d" % len(train_trees))
        print("First train tree: %s" % \
                Trees.PennTreeRenderer.render(train_trees[0]))
        print("Last train tree: %s" % \
                Trees.PennTreeRenderer.render(train_trees[-1]))

        # test data: MASC devtest
        print("Loading MASC test trees... from: ./data/parser/masc/devtest")
        test_trees.extend(read_masc_trees("./data/parser/masc/devtest", 0, 10))
        print("done.")
        print("Test trees size: %d" % len(test_trees))
        print("First test tree: %s" % \
                Trees.PennTreeRenderer.render(test_trees[0]))
        print("Last test tree: %s" % \
                Trees.PennTreeRenderer.render(test_trees[-1]))


    if data_set not in ["miniTest", "masc"]:
        raise Exception("Bad data set: %s: use miniTest or masc." % data_set)

    print("")
    print("Training parser...")
    parser.train(train_trees)

    print("Testing parser")
    test_parser(parser, test_trees, max_length)

