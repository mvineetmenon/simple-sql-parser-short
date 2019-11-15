import re


class Token(object):
    """ A simple Token structure.
        Contains the token type, value and position.
    """
    def __init__(self, type, val, pos):
        self.type = type
        self.val = val
        self.pos = pos

    def __str__(self):
        return '%s(%s) at %s' % (self.type, self.val, self.pos)


class LexerError(Exception):
    """ Lexer error exception.
        pos:
            Position in the input line where the error occurred.
    """
    def __init__(self, pos):
        self.pos = pos


class Lexer(object):
    """ A simple regex-based lexer/tokenizer.
        See below for an example of usage.
    """

    rules = [
        (r'\".*\"', 'STRING_LITERAL'),
        (r'\d+', 'NUMBER'),
        (r'\w+\(\)', 'SQL_FUNCTION'),
        (r"SELECT", 'SELECT'),
        (r",", 'SEPARATOR'),
        (r"IS", 'IS_OP'),
        (r"NOT", 'NEG_OP'),
        (r"NULL", 'NULL'),
        (r"ORDER", 'ORDER'),
        (r"BY", 'BY'),
        (r"INSERT", 'INSERT'),
        (r"INTO", 'INTO'),
        (r"\(", 'LP'),
        (r"\)", 'RP'),
        (r"VALUES", 'VALUES'),
        (r"DELETE", 'DELETE'),
        (r"FROM", 'FROM'),
        (r"WHERE", 'WHERE'),
        (r"[<>=]", 'EQ_OP'),
        (r"USE", 'USE'),
        (r"(\w+)((\.)(\w+))?", 'IDENTIFIER'),
        (r";", 'EOL')
    ]

    def __init__(self, buf):
        """ Create a lexer. """
        # All the regexes are concatenated into a single one
        # with named groups. Since the group names must be valid
        # Python identifiers, but the token types used by the
        # user are arbitrary strings, we auto-generate the group
        # names and map them to token types.
        #
        idx = 1
        regex_parts = []
        self.group_type = {}

        for regex, type in self.rules:
            groupname = 'GROUP%s' % idx
            regex_parts.append('(?P<%s>%s)' % (groupname, regex))
            self.group_type[groupname] = type
            idx += 1

        self.regex = re.compile('|'.join(regex_parts))
        self.skip_whitespace = True
        self.re_ws_skip = re.compile('\S')
        self.current_token = None

        # Initialize the buffer and position
        self.buf = buf
        self.pos = 0

    def next(self):
        """ Return the next token. None is returned if the end of the
            buffer was reached.
            LexerError is raised with the position of the error.
        """
        if self.pos >= len(self.buf):
            self.current_token = None
            return None
        else:
            if self.skip_whitespace:
                m = self.re_ws_skip.search(self.buf, self.pos)

                if m:
                    self.pos = m.start()
                else:
                    self.current_token = None
                    return None

            m = self.regex.match(self.buf, self.pos)
            if m:
                groupname = m.lastgroup
                tok_type = self.group_type[groupname]
                tok = Token(tok_type, m.group(groupname), self.pos)
                self.pos = m.end()
                self.current_token = tok
                return tok

            # if we're here, no rule matched
            raise LexerError(self.pos)

    def get_current_token(self):
        return self.current_token

