# vim: expandtab
# -*- coding: utf-8 -*-
# Vendored from Django 1.7's django/contrib/webdesign/lorem_ipsum.py
# (removed in Django 1.8).

from random import Random as _Random

COMMON_P = (u'Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor '
            u'incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud '
            u'exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure '
            u'dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. '
            u'Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt '
            u'mollit anim id est laborum.')

LOREM_IPSUM_WORDS = (u'exercitationem', u'perferendis', u'perspiciatis', u'laborum', u'eveniet',
    u'sunt', u'iure', u'nam', u'nobis', u'eum', u'cum', u'officiis', u'excepturi',
    u'odio', u'consectetur', u'quasi', u'aut', u'quisquam', u'vel', u'eligendi',
    u'itaque', u'non', u'odit', u'labore', u'saepe', u'est', u'sed', u'ipsum',
    u'dolor', u'sit', u'amet', u'tempora', u'voluptatibus', u'reprehenderit',
    u'aspernatur', u'aut', u'aut', u'repudiandae', u'consequuntur', u'voluptatem',
    u'receptis', u'rerum', u'modi', u'voluptas', u'doloremque', u'inventore',
    u'iste', u'dolorem', u'quasi', u'aut', u'blanditiis', u'libero', u'soluta',
    u'maxime', u'minima', u'in', u'nihil', u'in', u'harum', u'cumque',
    u'eligendi', u'facilis', u'quas', u'ipsa', u'provident', u'ab', u'aut',
    u'laudantium', u'at', u'molestias', u'recusandae', u'commodi', u'aut',
    u'fuga', u'repellendus', u'odio', u'tenetur', u'molestiae', u'labore',
    u'ut', u'exercitationem', u'dignissimos', u'eius', u'facere', u'quam',
    u'molestias', u'quis', u'voluptates', u'omnis', u'modi', u'eum', u'soluta',
    u'similique', u'et', u'excepturi', u'porro', u'labore', u'quis', u'assumenda',
)

_COMMON_WORDS = [u'lorem', u'ipsum', u'dolor', u'sit', u'amet', u'consectetur',
    u'adipisicing', u'elit', u'sed', u'do', u'eiusmod', u'tempor', u'incididunt',
    u'ut', u'labore', u'et', u'dolore', u'magna', u'aliqua']


def _sentence(rnd):
    word_list = list(LOREM_IPSUM_WORDS)
    rnd.shuffle(word_list)
    num_words = rnd.randint(5, 20)
    words = word_list[:num_words]
    words[0] = words[0].capitalize()
    return u' '.join(words) + u'.'


def _paragraph(rnd):
    num_sentences = rnd.randint(2, 6)
    return u' '.join(_sentence(rnd) for _ in range(num_sentences))


def paragraphs(count, common=True):
    u"""Return a list of ``count`` paragraphs of lorem ipsum text."""
    rnd = _Random()
    result = []
    if common:
        result.append(COMMON_P)
        count -= 1
    for _ in range(count):
        result.append(_paragraph(rnd))
    return result
