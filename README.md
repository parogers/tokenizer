Tokenizer
=========

Language tokenizer scripts written in Python. Currently there's only one 
program for parsing Javascript files.

Usage
-----

Run like this: "parsejs.py somefile.js" and the script will output a list 
of tokens, one per line, to stdout:

    var
    n
    =
    10
    ;
    if
    (
    n
    >=
    ....

There's a few options for filtering by token type. (eg print only strings) 
Mostly I use this to generate word clouds of my code. It's also useful for
extracting TODO comments as the script will treat an entire comment block
as a single token. (even multi-line comments)

Limitations
-----------

The program is implemented as a basic state machine that scans the input one
character at a time. (probably not the most efficient implementation) Likely
I've missed some corner cases. Also the parser does no language validation and
syntax errors in the language might be tokenized in odd ways.

