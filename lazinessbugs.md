Laziness bugs
=============

For various bugs which I have found in various programs, but have not reported, due to absent,
unresponsive, broken or otherwise user-hostile bug reporting systems. If you don't want my reports,
I'm happy to oblige.

The name "laziness bugs" is because it was originally true laziness. Then I started working down the
list, but the name stuck. It doesn't really mean anything anymore.

I try to report bugs through the official channels if available (or, if on GitHub and a fix is
obvious, I submit a PR). For example, I've submitted about 30 bugs in Wolfram|Alpha through the
feedback form at the bottom, most of which were fixed.

If anyone reading this knows of better report mechanisms than I could find, feel free to submit
these bugs there. No need to credit me, I'm happy if they're fixed.

If anyone reading this knows of any bugs you haven't found how to report, you're welcome to toss
them my way. It won't lead anywhere, but it won't do any harm either.

If any of these bugs are fixed or reported, ping me so I can remove them. I don't use all of these
anymore, and I wouldn't notice if they disappear. They're annotated with when I last encountered
them.


VirtualBox (Oracle)
-------------------

Not reported because reporting bugs requires an account, which wants my full, real name, and my
"work title", whatever that is for a student. I consider this privileged information and therefore
user hostile.

(Sep 2015) With a Swedish keyboard layout, VirtualBox calls the default Host key HÖGER CRTL. The
correct spelling is CTRL.

(Sep 2015) Manual, section 9.30: "In the future it might be possible to configure dedicated actions
but for there is only a warning in the log file." Missing a "now" in "but for there".

(Sep 2015) Manual, section 9.20.10 and 9.20.11: They're identical. I suspect one of them should
refer to keyboards instead.

(Sep 2015) Manual, various sections: There are references to chapter 11 all over, but that one is
empty. The content was moved to some kind of SDK thingy.


Firefox (Mozilla)
-----------------

Not reported due to poor responsiveness for my prior reports.

(May 2017) Visiting data:text/html,☃ autodetects the charset as ISO-8859-1 and prints â˜ƒ instead.
With the real character sitting right there in the title bar, mocking me.

(May 2017) Going to any data: URI and pulling the URL bar contents to the tab list does nothing.
Upon further inspection, it's throwing a "NS_ERROR_DOM_BAD_URI: Access to restricted URI denied"
error. data: shouldn't be restricted, the only thing whose contents are more public than data: is
about:blank.

(May 2016) Since version 46.0 (the GTK3 switch), many buttons (Page Bookmarked, for example) shrank
to about half height.

(May 2017) Version 46 also made the bottom pixel of a large dropdown menu (for example a bookmark
folder with 100 entries) non-interactive, so I can't drag a tab into a huge folder and wave it
around until I reach the bottom.

(Dec 2015) ![Downloaded file: 411.2744140625KB](https://github.com/Alcaro/misctoys/blob/master/firefoxbug.png)

(May 2017) Add `https://*.example.com` to the cookie whitelist. Result: `http://https`


Thunderbird (Mozilla)
-----------------

Not reported due to poor responsiveness for my prior reports.

(May 2017) Receive an email with only Return-Path, Delivered-To and Received headers; no title,
recipient, sender or body. It marks the email account as having something unread, but doesn't show
up anywhere and can't be marked read.

(May 2017) On Lubuntu 17.04, the tabs under Preferences->Security are completely unstyled and don't
look clickable.


.NET Foundation (Microsoft)
---------------------------

Not reported due to (1) requiring a CLA full of legalese I can barely read (2) the public sample CLA
(which I assume is accurate) requiring my real name, signature, postal address, and some other stuff
I'm not too eager to give to the company behind the Windows 10 privacy scare (3) their privacy
policy being an even bigger pile of even less legligible legalese (4) their privacy policy not even
mentioning the obvious collection of personal information going on around those CLAs.

(Sep 2015) [Reported but bot-rejected](https://github.com/dotnet/coreclr/pull/1644): Contribution
guide typos Wikipedia as wikipedia, and they forgot a link to the .NET Foundation forums right in
the main repo readme. Maybe their humans will merge it anyways, since a copypasted link and a W
obviously fails the [threshold of originality](https://en.wikipedia.org/wiki/Threshold_of_originality),
but probably not.


Ubuntu (Canonical), or whoever their upstreams are
--------------------------------------------------

Not reported because it requires an account, which requires my name, and a privacy policy mentioning
credit cards. No thanks.

(Sep 2015) python3-commandnotfound: Typing (or pasting) ``` `echo -e '\xC0'` ``` into a shell throws a 35-line
error about "'utf-8' codec can't encode character '\udcc0' in position 0: surrogates not allowed".
While I can't really expect any real suggestions from that, walls of text bigger than my terminal
aren't really the best solution. Where did DCC0 come from, anyways?

(May 2017) gnome-mplayer: Name a file 'We Are #1.webm', open it. Result: "File 'We Are ' not found".

(May 2017) Somewhere in the Lubuntu login manager: The default pic (not sure if it's changeable) is
a blurry mess.


Erlang Solutions
----------------

Not reported because the contact page points only to a community site with no obvious bug report
mechanism, and to their physical offices. I'm not going to Stockholm to report bugs.

(Oct 2015) [At least one of these Erlang packages](https://www.erlang-solutions.com/downloads/download-erlang-otp)
reports a dependency on libwxgtk3.0-0 or libwxgtk2.8-0. Unfortunately, dpkg defaults to the former,
while it only actually works with the latter. Only an optional, and clearly uncommon,
Erlang module depends on that, so it's understandable that it got missed, but still a bug.


Gmail (Google)
--------------

Not reported because I can't find the bug report form. All I find, both in Settings, Help and
googling, is irrelevant nonsense and a few Google Groups posts that no longer point anywhere.

(Nov 2015) Attach a file of size zero. It's too big and ends up on Google Drive.

(Nov 2015) Then the Drive form is a blob of \<div contenteditable="false" blah blah>. In text form.
It shows up as a big blob of technobabble for the recipient, even if the recipient is also on Gmail
(it also shows up in the attachment list, but only on the Gmail web interface). Didn't test if this
Drive form is screwed up if the file really is that big, or only for zero-size files.


Python3 chardet (Ian Cordasco or Dan Blanchard)
-----------------------------------------------

Not reported because [you tell me where the bug report form is](https://pypi.python.org/pypi/chardet).
That PyPI Bug Reports link doesn't count, it's for bugs in PyPI itself.

(Apr 2016)
```
$ python3
>>> import chardet
>>> chardet.detect(bytearray())
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/usr/lib/python3/dist-packages/chardet/__init__.py", line 25, in detect
    raise ValueError('Expected a bytes object, not a unicode object')
ValueError: Expected a bytes object, not a unicode object
```

That's not a unicode object.


Visual Studio (Microsoft)
-------------------------

Reported about six of those via the built-in reporter. No response, and they don't show up on search
engines either, so I'll just rant here instead.

(May 2016) I found a huge number of bugs in this product, so I'm shoving them off to
[their own file](vstudiobugs.md).


GCC (GNU or FSF, not sure)
--------------------------

Not reported due to poor responsiveness for prior reports.

(Mar 2018)
```
void x() { __builtin_unreachable(); }
void y() { __builtin_unreachable(); }

typedef void(*fptr)();
__attribute__((noinline)) fptr noopt(fptr z) { return z; }

bool lol1() { return x == y; }
bool lol2() { return x == noopt(y); }
```

Under -O3, lol1 is optimized to 'return false', while x and y are optimized to zero bytes and lol2
ends up returning true. Both true and false are fine, but inconsistency is a bug. The ideal fix
would be to stick their labels in the middle of other functions; a much easier fix would be emitting
some arbitrary single byte. ret would be the obvious choice, but int3 would be better (or ud2,
though that's two bytes).

(Mar 2019)
Similarly,
```
#include <stdio.h>

struct a {};
void x(a a1, a a2) { printf("%p == %p? %d\n", &a1, &a2, &a1 == &a2); }

int main()
{
    x(a(),a());
}
```

gives a1 and a2 the same address, but claims they're not equal. (Only works for function arguments.)
