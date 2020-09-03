import nltk
import re

class Context:
    def __init__(self, contents):
        self._words = nltk.word_tokenize(contents)
        self._tagged_words = nltk.pos_tag(self._words)

    def generate(self):
        words = ' '.join(self._words)

        # clean up
        words = re.sub(r" (n\'t|'\w+)\b", r'\1', words)      # contractions
        words = re.sub("(''|``)", '"', words)                # quotes
        words = re.sub(' ([.,?!)])', r'\1', words)           # left-associative
        words = re.sub('([(]) ', r'\1', words)               # right-associative
        words = re.sub(r'\b(gon|wan) na\b', r'\1na', words)  # "gonna" / "wanna"
        words = words.capitalize()

        return words

    def get(self, position):
        return self._tagged_words[position]

    def set(self, position, value):
        self._words[position] = value
        self._tagged_words = nltk.pos_tag(self._words)

    def nouns(self):
        for i, (word, tag) in enumerate(self._tagged_words):
            if tag[0] == 'N':
                yield Token(self, i)

class Token:
    def __init__(self, context, position):
        self._context = context
        self._position = position

    def get(self):
        return self._context.get(self._position)

    def set(self, value):
        return self._context.set(self._position, value)
