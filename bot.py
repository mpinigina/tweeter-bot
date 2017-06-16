import re
import tweepy
import argparse
from time import sleep
from credentials import *
from random import uniform
from collections import defaultdict

r_alphabet = re.compile(u'[а-яА-Я0-9-]+|[.,:;?!]+')


def get_args():
    parser = argparse.ArgumentParser(description='tweets random phrases')
    parser.add_argument('query', type=str,
                        help='search keyword fot twitter')
    return parser.parse_args()


def get_lines(file):
    with open(file, 'r') as f:
        return f.readlines()


def get_tokens(lines):
    for line in lines:
        for token in r_alphabet.findall(line.strip()):
            yield token


def gen_trigrams(tokens):
    t0, t1 = '$', '$'
    for t2 in tokens:
        yield t0, t1, t2
        if t2 in '.!?':
            yield t1, t2, '$'
            yield t2, '$', '$'
            t0, t1 = '$', '$'
        else:
            t0, t1 = t1, t2


def train(corpus):
    lines = get_lines(corpus)
    tokens = get_tokens(lines)
    trigrams = gen_trigrams(tokens)
    bi, tri = defaultdict(lambda: 0.0), defaultdict(lambda: 0.0)

    for t0, t1, t2 in trigrams:
        bi[t0, t1] += 1
        tri[t0, t1, t2] += 1

    model = {}
    for (t0, t1, t2), freq in tri.items():
        if (t0, t1) in model:
            model[t0, t1].append((t2, freq / bi[t0, t1]))
        else:
            model[t0, t1] = [(t2, freq / bi[t0, t1])]
    return model


def generate_sentence(model):
    phrase = ''
    t0, t1 = '$', '$'
    while 1:
        t0, t1 = t1, unirand(model[t0, t1])
        if t1 == '$':
            break
        if t1 in ('.!?,;:') or t0 == '$':
            phrase += t1
        else:
            phrase += ' ' + t1
    return phrase.capitalize()


def unirand(seq):
    sum_, freq_ = 0, 0
    for item, freq in seq:
        sum_ += freq
    rnd = uniform(0, sum_)
    for token, freq in seq:
        freq_ += freq
        if rnd < freq_:
            return token


if __name__ == '__main__':
    args = get_args()
    query = args.query
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)
    model = train('tolstoy.txt')

    for tweet in tweepy.Cursor(api.search, q=query, lang='ru').items():
        try:
            if (not tweet.retweeted and 'RT @' not in tweet.text and
                    tweet.text.endswith('?')):
                random_phrase = generate_sentence(model)
                api.update_status('@{} {} https://twitter.com/{}/status/{}'.format(
                    tweet.user.screen_name,
                    random_phrase,
                    tweet.user.screen_name,
                    tweet.id), in_reply_to_status_id=tweet.id)
        except tweepy.TweepError:
            sleep(60 * 15)
            continue
