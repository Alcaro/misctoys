#!/usr/bin/env python3
# things I dislike about Python

# catching SIGINT by default; ^C should always terminate the process, even if it's currently
#  awaiting GUI events or otherwise not executing python code
# (and even when the KeyboardInterrupt is raised, many GUI frameworks and tools just print the exception and discard it without terminatíng)

# python ternary is middle endian, and inconsistent with most other programming languages
# being written in english pronunciation order is a valid argument, but it's weak
# it's much more important to have similar and related clauses near each other, and to write things in evaluation order
print(3 if True else 5)
print(3 if False else 5)

# .join() is also middle endian, and looks weird together with .split()
# (it's little endian if the iterable is simple enough, but little endian code is still wrong)
','.join("1,2,3".split(',')[::-1])
','.join(["1","2","3"])

# ignoring type hints; they should either be enforced or look like comments
def f(a:int, b:int)->dict: return a+b
print(f("abc","def"))

# is this type safe? Depends on who you ask! Mypy says yes, because lst's inferred type is List[Tuple[int,int]].
# Pyright says no, because lst is List[Tuple[Literal[1],Literal[2]]].
lst = [(1,2)]
lst.append((3,4))

# __pycache__ belongs in /tmp or in /dev/null

# flattening nested lists, again, has endian issues
xss = [[1,2],[3],[],[4]]
print([x  for xs in xss  for x in xs])
# print([x  for x in xs  for xs in xss]) would be a lot less ugly, or print([for xs in xss  for x in xs  select x])

# dir() and id() are too rare, and too valuable as variable names, to be builtin auto-imported functions
print(dir(1))
print(id(1))
# most builtins are dubious; they should be member functions on their applicable type (usually Iterable),
#  moved into the math module, or otherwise not be auto-imported

print("abcde"[:-3])  # "ab"
print("abcde"[:-2])  # "abc"
print("abcde"[:-1])  # "abcd"
print("abcde"[:-0])  # ""
# should've been [:~3], [:~2], [:~1], [:~0]
# "abcde"[:None] is "abcde", and you can use "abcde"[:len("abcde")-0], but ~ would've been smoother

# functions' default arguments are only evaluated once, not on every call
def g(l=[]):
	l.append(5)
	print(l)
g()  # [5]
g()  # [5, 5]
# same goes for classes, have to set it in __init__()
class my_cls:
	member1 = []
	def __init__(self):
		self.member2 = []
a = my_cls()
b = my_cls()
a.member1.append(50)
a.member2.append(51)
print(b.member1, b.member2)

# no errors or warnings for defining the same thing twice
def a(): pass
def a(): pass
class b: pass
class b:
	def c(self): pass
	def c(self): pass

def fn():
	# this returns an empty iterator; the 3 is discarded, with no error
	# while a plain return is a reasonable way to stop an iterator, returning an expression from an iterator function should be a syntax error
	return 3
	if False:
		yield 0
print(list(fn()))

print(bool(str(False)))  # it's unexpectedly True. Though I'm not entirely sure what would be a better behavior.

# the XML parsers enable several dangerous features by default https://docs.python.org/3/library/xml.html#xml-vulnerabilities

# the hashmap iteration fiasco - made it impossible to compare dicts between runs, and was backported all over
# and then they chose to repeat that fiasco with int("1"*5000)

# indentation based syntax - easy to get mixed tabs and spaces and all kinds of fun errors,
# doesn't allow making debug code more prominent by removing indentation,
# and doesn't allow removing the indent if 95% of the file is in the same class

# the GIL - Python 1 was created long before threading was relevant (1994 vs 2008), and backwards
# compat constraints make it hard to fix, but it's still a problem

# backwards stack traces - it's debatable which direction is better, but being different from
# everything else is definitely not better

# the core devs vigorously defend several of the above, claiming that they're more intuitive or
# helpful; while they're better in some ways, they are worse in other ways, and the sum is strongly
# negative. To me, most of the above look like implementation constraints (for example, Iterable is
# a pure virtual interface, there's no base class in which to implement .all() or .join()),
# artifacts of early Python development (GIL), and/or backwards compatibility with decisions that
# were wrong even when they were made (but perhaps Python was the first language to make that
# choice, so nobody knew how wrong they are).
