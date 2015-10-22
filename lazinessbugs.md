Laziness bugs
=============

For various bugs which I have found in various programs, but have not reported, due to absent,
unresponsive or user-hostile bug reporting systems. If you don't want my reports, I'm happy to
oblige.

The name "laziness bugs" is because it was originally true laziness. Then I started working down the
list, but the name stuck. It doesn't really mean anything anymore.

I try to report bugs through the official channels if available (or, if on GitHub and a fix is
obvious, I submit a PR). For example, I've submitted about 30 bugs in Wolfram|Alpha through the
feedback form at the bottom, several of which are reported fixed.

If anyone reading this wants to report these bugs, feel free to. No need to credit me, I'm happy if
they're fixed.

VirtualBox (Oracle)
-------------------

Not reported because reporting bugs requires an account, which wants my full, real name, and my
"work title", whatever that is for a student. I consider this privileged information and therefore
user hostile.

With a Swedish keyboard layout, VirtualBox calls the default Host key HÖGER CRTL. The correct
spelling is CTRL.

Manual, section 9.30: "In the future it might be possible to configure dedicated actions but for
there is only a warning in the log file." Missing a "now" in "but for there".

Manual, section 9.20.10 and 9.20.11: They're identical. I suspect one of them should refer to
keyboards instead.

Manual, various sections: There are references to chapter 11 all over, but that one is empty. The
content was moved to some kind of SDK thingy.

Firefox (Mozilla)
-----------------

Not reported due to poor responsiveness for my prior reports.

Visiting data:text/html,☃ autodetects the charset as ISO-8859-1 and prints â˜ƒ instead. With the
real character sitting right there in the title bar, mocking me.

Going to any data: URI and pulling the URL bar contents to the tab list does nothing. Upon further
inspection, it's throwing a "NS_ERROR_DOM_BAD_URI: Access to restricted URI denied" error. data:
shouldn't be restricted, the only thing whose contents are more public than data: is about:blank.

.NET Foundation (Microsoft)
---------------------------

Not reported due to (1) requiring a CLA full of legalese I can barely read (2) the public sample CLA
(which I assume is accurate) requiring my real name, signature, postal address, and some other stuff
I'm not too eager to give to the company behind the Windows 10 privacy scare (3) their privacy
policy being an even bigger pile of even less leglible legalese (4) their privacy policy not even
mentioning the obvious collection of personal information going on around those CLAs.

[Reported but bot-rejected](https://github.com/dotnet/coreclr/pull/1644): Contribution guide typos
Wikipedia as wikipedia, and they forgot a link to the .NET Foundation forums right in the main repo
readme. Maybe their humans will merge it anyways, since a copypasted link and a W obviously fails
the [threshold of originality](https://en.wikipedia.org/wiki/Threshold_of_originality), but probably
not.

Ubuntu (Canonical), or whoever their upstream for python3-commandnotfound is
----------------------------------------------------------------------------

Not reported because it requires an account and I don't want to create yet another.

Typing (or pasting) ``` `echo -e '\xC0'` ``` into a shell throws a 35-line error about "'utf-8'
codec can't encode character '\udcc0' in position 0: surrogates not allowed". While I can't really
expect any real suggestions from that, walls of text bigger than my terminal aren't really the best
solution. Where did DCC0 come from, anyways?

(Originally found by typoing something in PuTTY. Its default charset is ISO-8859-1; combine that
with a Swedish keyboard, where we have åäö, invalid UTF-8 is rather easy.)

Erlang Solutions
----------------

Not reported because the contact page points only to a community site with no obvious bug report
mechanism, and to their physical offices. I'm not going to Stockholm to report bugs.

[At least one of these Erlang packages](https://www.erlang-solutions.com/downloads/download-erlang-otp)
reports a dependency on libwxgtk3.0-0 or libwxgtk2.8-0. Unfortunately, dpkg defaults to the former,
while it only actually works with the latter. Only an optional, and clearly uncommon,
Erlang module depends on that, so it's understandable that it got missed, but still a bug.
