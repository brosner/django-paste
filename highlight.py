from pygments.lexers import get_all_lexers, get_lexer_by_name
from pygments.styles import get_all_styles
from pygments.formatters import HtmlFormatter
from pygments import highlight

LEXER_LIST_ALL = sorted([(i[1][0], i[0]) for i in get_all_lexers()])
LEXER_LIST = (
    ('apacheconf', 'ApacheConf'),
    ('as', 'ActionScript'),
    ('bash', 'Bash'),
    ('bbcode', 'BBCode'),
    ('c', 'C'),
    ('cpp', 'C++'),
    ('csharp', 'C#'),
    ('css', 'CSS'),
    ('diff', 'Diff'),
    ('django', 'Django/Jinja'),
    ('erlang', 'Erlang'),
    ('html', 'HTML'),
    ('ini', 'INI'),
    ('irc', 'IRC logs'),
    ('java', 'Java'),
    ('js', 'JavaScript'),
    ('jsp', 'Java Server Page'),
    ('lua', 'Lua'),
    ('make', 'Makefile'),
    ('perl', 'Perl'),
    ('php', 'PHP'),
    ('pot', 'Gettext Catalog'),
    ('pycon', 'Python console session'),
    ('pytb', 'Python Traceback'),
    ('python', 'Python'),
    ('python3', 'Python 3'),
    ('rb', 'Ruby'),
    ('rst', 'reStructuredText'),
    ('smarty', 'Smarty'),
    ('sql', 'SQL'),
    ('text', 'Text only'),
    ('xml', 'XML'),
    ('yaml', 'YAML')
)
LEXER_DEFAULT = 'text'


class NakedHtmlFormatter(HtmlFormatter):
    def wrap(self, source, outfile):
        return self._wrap_code(source)
    def _wrap_code(self, source):
        for i, t in source:
            yield i, t

def pygmentize(code_string, lexer_name='text'):
    return highlight(code_string, get_lexer_by_name(lexer_name), NakedHtmlFormatter())