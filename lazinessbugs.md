Laziness bugs
=============

For various bugs which I have found in various programs, but have not reported, due to absent,
unresponsive or user-hostile bug reporting systems. If you don't want my reports, I'm happy to
oblige.

VirtualBox (Oracle)
-------------------

Not reported because reporting bugs requires an account, which wants my full, real name, and my
"work title", whatever that is for a student. I consider this user hostile.

With a Swedish keyboard layout, VirtualBox calls the default Host key HÖGER CRTL. The correct
spelling is CTRL.

Manual, section 9.30. "In the future it might be possible to configure dedicated actions but for
there is only a warning in the log file." Missing a "now" in "but for there".

Manual, section 9.20.10 and 9.20.11: They're identical. I suspect one of them should refer to
keyboards instead.

Manual, various sections: There are references to chapter 11 all over, but that one is empty. The
content was moved to some kind of SDK thingy.

Firefox (Mozilla)
-----------------

Not reported due to poor responsiveness for my prior reports.

Visiting data:text/html,ø autodetects the charset as ISO-8859-1 and prints Ã¸ instead. With the real
character sitting right there in the title bar, mocking me.

Going to any data: URI and drawing the URL bar contents to the tab list does nothing. Upon further
inspection, it's throwing a "NS_ERROR_DOM_BAD_URI: Access to restricted URI denied" error. The only
thing that should be less restricted than data: is about:blank.

Ubuntu (Canonical), or whoever made command-not-found
-----------------------------------------------------

Not reported because it requires an account and I don't want to create yet another.

`echo -e '\xC0'` throws a "'utf-8' codec can't encode character '\udcc0' in position 0: surrogates
not allowed" exception. While I can't really expect any real suggestions from that, an exception is
probably wrong way to handle it.
