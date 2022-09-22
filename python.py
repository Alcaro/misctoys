#!/usr/bin/env python3
# things Python do wrong

# catching SIGINT by default; ^C should always terminate the process, even if it's currently
#  awaiting GUI events or otherwise not executing python code
# (and even when the KeyboardInterrupt is raised, many GUI tools just print the exception and discard it without terminatíng)

# python ternary is middle endian, and inconsistent with most other programming languages
# being written in english pronunciation order is a valid argument, but it's weak
# it's much more important to have similar and related clauses near each other, and to write things in evaluation order
3 if True else 5

# .join() is also middle endian, and looks weird together with .split()
# (it's little endian if the iterable is simple enough, but little endian code is still wrong)
','.join("1,2,3".split(',')[::-1])
','.join(["1","2","3"])

# ignoring type hints; they should either be enforced or look like comments
def f(a:int, b:int): return a+b
f("abc","def")

# __pycache__ belongs in /tmp or in /dev/null

# flattening nested lists, again, has endian issues
xss = [[1,2],[3],[],[4]]
print([x for xs in xss for x in xs])

# dir() and id() are too rare, and too valuable as variable names, to be builtin auto-imported functions
print(dir(5))
print(id(5)))
# most builtins are dubious; they should be member functions on their applicable type (usually
# Iterable), moved into the math module, or otherwise not be auto-imported

"abcde"[:-3]  # "ab"
"abcde"[:-2]  # "abc"
"abcde"[:-1]  # "abcd"
"abcde"[:-0]  # ""
# should've been [:~3], [:~2], [:~1], [:~0]

# functions' default arguments are only evaluated once, not on every call
def g(l=[]):
	l.append(5)
	print(l)
g()  # [5]
g()  # [5, 5]
# same goes for classes; class my_cls: member=[] lets every my_cls share a single list

# no errors or warnings for defining the same thing twice
def a(): pass
def a(): pass
class b: pass
class b:
	def c(self): pass
	def c(self): pass

def fn():
	# this returns an empty iterator; the 5 is discarded, with no error
	# while a plain return is a reasonable way to stop an iterator, returning an expression from an iterator function should be a syntax error
	return 5
	if False:
		yield 0

# indentation based syntax - easy to get mixed tabs and spaces and all kinds of fun errors, doesn't
# allow making debug code more prominent by removing indentation, and doesn't allow removing the
# indent if 95% of the file is in the same class

# the GIL - Python 1 was created long before threading was relevant (1994 vs 2008), and backwards
# compat constraints make it hard to fix, but it's still a problem

# backwards stack traces - it's debatable which direction is better, but being different from
# everything else is definitely not better

# the core devs vigorously defend several of the above, claiming that they're more intuitive or
# helpful; while they're better in some ways, they are worse in other ways, and the sum is strongly
# negative. To me, the above look like implementation constraints (for example, Iterable is a pure
# virtual interface, there's no base class in which to implement .all()), artifacts of early Python
# development (GIL), and/or backwards compatibility with decisions that were wrong even when they
# were made (but perhaps nobody knew how wrong they are).
