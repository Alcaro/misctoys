#!/usr/bin/env python3
# things I dislike about Python

# catching SIGINT by default; ^C should always terminate the process, even if it's currently
#  awaiting GUI events or otherwise not executing python code
# (and even when the KeyboardInterrupt is raised, many GUI frameworks and tools just
#  print the exception and discard it without terminatíng)

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
# (oh, and every Python reformatter tool I'm aware of would remove the double spaces from the above, making it near impossible to parse)

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
# "abcde"[-0 or None] is reasonably short, but it looks like token soup unless you've seen it before

print("abcde"[3:9])  # it's "de". I'd expect an IndexError.

# functions' default arguments are only evaluated once, not on every call
def g(l=[]):
	l.append(5)
	return l
print(g())  # [5]
print(g())  # [5, 5]
# same goes for classes, have to set it in __init__()
class my_cls:
	member1 = []
	def __init__(self):
		self.member2 = []
a = my_cls()
b = my_cls()
a.member1.append(50)
a.member2.append(51)
print(b.member1, b.member2)  # [50] []

global1 = []
def a():
	global1.append(5)  # this works
a()
global2 = 5
def b():
	global2 += 1  # this doesn't
try:
	b()
except UnboundLocalError:
	pass

print(hex(123))  # includes a 0x prefix. Every other hex formatting instruction I'm aware of in every language defaults to excluding it.

# no errors or warnings for defining the same thing twice
def a(): pass
def a(): pass
class b: pass
class b:
	def c(self): pass
	def c(self): pass

# Exactly one of these four will print in different order between runs.
a={1,2,3,4,5}
b={1:1,2:2,3:3,4:4,5:5}
c={"a","b","c","d","e"}
d={"a":1,"b":2,"c":3,"d":4,"e":5}
print(a)
print(b)
print(c)
print(d)
# This changed in Python 3.2.3; before that, all were consistent order. Introducing behavioral changes in minor versions is impolite.
# Similarly, int("1"*5000) was disabled in 3.10.7, 3.9.14, 3.8.14 and 3.7.14.

print("\S")  # it's the two characters \ S; in a sane language, unknown escapes are an error
# (it prints a warning since Python 3.12. Better late than never...)

class eee:
	MY_VALUE = 42
	# one of these demands to be prefixed with class name, the other demands the opposite
	def a(self, arg = MY_VALUE):
		return arg + eee.MY_VALUE
print(eee().a())

print("☃" in open(__file__).read())  # this will find the snowman on this line, right? You sure? Did you try it on Windows?
# (may be fixed in Python 3.15 <https://peps.python.org/pep-0686/>, but the relevant documentation is wildly incomplete and contradictory)

def fn():
	# this returns an empty iterator; the 3 is discarded, with no error
	# while a plain return is a reasonable way to stop an iterator, returning an expression from an iterator function should be a syntax error
	return 3
	if False:
		yield 0
print(list(fn()))

print(bool(str(False)))  # it's unexpectedly True. Though both functions are sane on their own, I don't know how to fix that.

# the XML parsers enable several dangerous features by default https://docs.python.org/3/library/xml.html#xml-vulnerabilities

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
