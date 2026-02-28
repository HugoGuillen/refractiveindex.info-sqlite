from collections import namedtuple

Shelf = namedtuple('Shelf', ['shelf', 'name'])
Book = namedtuple('Book', ['book', 'name'])
Page = namedtuple('Page', ['page', 'name', 'path'])
Entry = namedtuple('Entry', ['id', 'shelf', 'book', 'page'])
