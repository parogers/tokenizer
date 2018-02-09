#!/usr/bin/env python3

from io import StringIO
import argparse
import string
import sys

class Reader:
    """A filestream wrapper that allows bytes to be 'unread' (pushed back
    into the stream. Subsequent reading pulls them out of an internal buffer.
    Once the buffer is exhausted, reading from stream continues normally."""
    def __init__(self, stream):
        self.stream = stream
        # The buffer of 'unread' characters
        self.buffer = []

    def read(self):
        if (self.buffer):
            b = self.buffer[0]
            del self.buffer[0]
            return b
        return self.stream.read(1)

    def unread(self, b):
        self.buffer.append(b)

def read_tokens(stream):
    """Iterates over the Javascript tokens in the stream. A token is anything
    that could be considered a high-level 'piece' of the language:

        Any language keyword, variable names and function names
        An entire single-line comment
        An entire multi-line comment block
        An opening or close brace
        Any language operator from "<>[]*+-=|&"
        The end of line semi-colan, or as part of a construct like 'for'
        Numeric values
        An entire string from open quote to close quote
    """
    ID_CHARS = string.ascii_letters + string.digits + "_"
    HEX_CHARS = string.digits + "ABCDEF"
    OP_CHARS = "<>=&|~!"

    reader = Reader(stream)
    in_tick_string = False
    in_quote_string = False
    multi_comment = False
    single_comment = False
    number_value = False
    symbol_value = False
    compare_value = False
    token = ""
    last = ""
    while True:
        ch = reader.read()
        if (not ch):
            break

        if (in_quote_string or in_tick_string):
            if ((in_quote_string and ch == "\"" or
                 in_tick_string and ch == "'") and last != "\\"):
                in_quote_string = False
                in_tick_string = False
                token += ch
                yield ('string', token)
            else:
                token += ch

        elif (single_comment):
            if (ch == "\n"):
                single_comment = False
                yield ('comment', token)
            else:
                token += ch

        elif (multi_comment):
            if (last == "*" and ch == "/"):
                multi_comment = False
                token += ch
                yield ('comment', token)
            else:
                token += ch

        elif (number_value):
            if (token == "0" and ch == "x" or
                token.startswith("0x") and ch.upper() in HEX_CHARS):
                # Hex value
                token += ch
            elif (ch in string.digits or ch == "."):
                token += ch
            else:
                reader.unread(ch)
                yield ('number', token)
                number_value = False

        elif (symbol_value):
            if (ch in ID_CHARS):
                token += ch
            else:
                reader.unread(ch)
                yield ('symbol', token)
                symbol_value = False

        elif (compare_value):
            if (ch in OP_CHARS):
                token += ch
            else:
                reader.unread(ch)
                yield ('operator', token)
                compare_value = False

        else:
            if (ch == "/"):
                # A single slash might be the start of a single-line comment
                # a multi-line comment, or a division. Fortunately we can 
                # figure out all of this by peeking at the next character.
                nch = reader.read()
                if (nch == "/"):
                    single_comment = True
                    token = "//"
                elif (nch == "*"):
                    multi_comment = True
                    token = "/*"
                else:
                    # Just a division symbol. Push it back into the stream
                    token = ch
                    compare_value = True
                    reader.unread(nch)

            elif (last != "\\" and ch == "\""):
                in_quote_string = True
                token = ch

            elif (last != "\\" and ch == "'"):
                in_tick_string = True
                token = ch

            elif (ch in string.digits):
                number_value = True
                token = ch

            elif (ch in ID_CHARS):
                symbol_value = True
                token = ch
            
            elif (ch in OP_CHARS):
                compare_value = True
                token = ch

            elif (not ch in " \t\n\r"):
                yield ('operator', ch)

        last = ch

if (__name__ == "__main__"):
    parser = argparse.ArgumentParser(
        description="Parse over a .js file and print the tokens")
    parser.add_argument(
        "--names", "-n", action="store_true", default=False,
        help="Print only name-like tokens (language keywords, variable and function names)")
    parser.add_argument(
        "--comments", "-c", action="store_true", default=False,
        help="Print only comment tokens")
    parser.add_argument(
        "--ignore", "-i", default="",
        help="Tokens to ignore in output (comma separated)")
    parser.add_argument(
        "--nice", "-N", action="store_true", default=False,
        help="Attempts to make the output easier to read")
    parser.add_argument(
        "--search", "-s", default="",
        help="Only output tokens matching the given search string")
    parser.add_argument(
        "src", nargs="*", default="-",
        help="The .js source file (optional, defaults to stdin)")
    args = parser.parse_args()

    ignore = args.ignore.split(",")
    if (args.nice): 
        end = " "
        out_stream = StringIO()
    else: 
        end = None
        out_stream = sys.stdout

    for src in args.src:
        if (src == "-"):
            stream = sys.stdin
        else:
            stream = open(src)

        for (token_type, token) in read_tokens(stream):
            if (token in ignore):
                continue
            # TODO - support RE?
            if (args.search and not(args.search in token)):
                continue

            if (args.names):
                # Only printing name-like things
                if (token_type == "symbol"):
                    print(token, end=end, file=out_stream)
            elif (args.comments):
                # Only printing comments
                if (token_type == "comment"):
                    print(token, end=end, file=out_stream)
            else:
                # Print everything
                print(token, end=end, file=out_stream)

    if (args.nice):
        txt = out_stream.getvalue()
        txt = txt.replace(' ( ', '(').replace(' ) ', ')')
        txt = txt.replace(' [ ', '[').replace(' ] ', ']')
        txt = txt.replace(' ,', ',')
        txt = txt.replace(' . ', '.')
        txt = txt.replace(';', ';\n').replace(' ;', ';')
        txt = txt.replace('{ ', '{\n')
        txt = txt.replace('} ', '}\n')
        print(txt)

