import sublime
import sublime_plugin
import re

SCOPE_VAR = 'meta.variable.haxe.2'
SCOPE_VAR_NAME = 'entity.name.variable.haxe.2'
SCOPE_FUNC = 'meta.method.haxe.2'
SCOPE_FUNC_BLOCK = 'meta.method.block.haxe.2'
SCOPE_FUNC_NAME = 'entity.name.function.haxe.2'
SCOPE_STATIC = 'meta.static.haxe.2'
SCOPE_TYPE = 'meta.type'
SCOPE_TYPE_BLOCK = 'meta.type.block.haxe.2'
SCOPE_TYPE_NAME = 'entity.name.type.class.haxe.2'

FIELD_FUNC = 'function'
FIELD_VAR = 'var'
FIELD_STATIC_FUNC = 'static function'
FIELD_STATIC_VAR = 'static var'

re_format_op_par = re.compile('\s*\(\s*')
re_format_cl_par = re.compile('\s*\)')
re_format_empty_par = re.compile('\(\s+\)')
re_format_colon = re.compile('([^\d\s])\s*:\s*')
re_format_op_ang = re.compile('\s*<\s*')
re_format_cl_ang = re.compile('([^-\s])\s*>')
re_format_comma = re.compile('\s*,\s*')
re_format_assign = re.compile('\s*=\s*')
re_format_type_sep = re.compile('\s*->\s*')
re_format_semicolon = re.compile('\s*;')

re_word = re.compile('^[_a-z]\w*$')
re_whitespace_style = re.compile(
    'function f(\s*)\((\s*)'
    'a(\s*):(\s*)T(\s*)<(\s*)T(\s*)>(\s*),(\s*)'
    'b\s*:\s*T(\s*)=(\s*)null(\s*)'
    '\)\s*:\s*T(\s*)->(\s*)T(\s*);')
whitespace_style = None


def count_blank_lines(view, pos):
    whitespaces = ' \t'
    src = view.substr(sublime.Region(0, view.size()))
    before, after = 0, 0

    for i in range(pos - 1, 0, -1):
        c = src[i]
        if c == '\n':
            before += 1
        elif c not in whitespaces:
            break

    for i in range(pos, view.size()):
        c = src[i]
        if c == '\n':
            after += 1
        elif c not in whitespaces:
            break

    return before, after


def filter_regions(inners, outers):
    contains = []
    ncontains = []
    ii, io, ni, no = 0, 0, len(inners), len(outers)

    if no == 0:
        return contains, inners[:]

    while io < no and ii < ni:
        inner = inners[ii]
        outer = outers[io]

        if outer.contains(inner):
            contains.append(inner)
            io += 1
            ii += 1
            continue

        if inner.begin() > outer.begin():
            io += 1
        else:
            ncontains.append(inner)
            ii += 1

    while ii < ni:
        ncontains.append(inners[ii])
        ii += 1

    return contains, ncontains


def find_cur_region(view, selector, as_string=False):
    rgns = view.find_by_selector(selector)
    pos = view.sel()[0].begin()

    for rgn in rgns:
        if rgn.contains(pos):
            if as_string:
                return view.substr(rgn)
            else:
                return rgn

    return None


def find_line_start_pos(view, pos):
    rgn = view.line(pos)
    pos = rgn.begin()
    line = view.substr(rgn)
    for c in line:
        if c == ' ' or c == '\t':
            pos += 1
        else:
            break

    return pos


def find_regions(view, selector, in_region=None, incl_string=False):
    rgns = view.find_by_selector(selector)
    regions = []

    for rgn in rgns:
        if in_region is not None and in_region.contains(rgn):
            if incl_string:
                regions.append((rgn, view.substr(rgn)))
            else:
                regions.append(rgn)

    return regions


def format_statement(view, value):
    ws = get_whitespace_style(view)

    value = re_format_op_par.sub('%s(%s' % (ws['_('], ws['(_']), value)
    value = re_format_cl_par.sub('%s)' % ws['_)'], value)
    value = re_format_empty_par.sub('()', value)
    value = re_format_colon.sub('\\1%s:%s' % (ws['_:'], ws[':_']), value)
    value = re_format_op_ang.sub('%s<%s' % (ws['_<'], ws['<_']), value)
    value = re_format_cl_ang.sub('\\1%s>' % ws['_>'], value)
    value = re_format_comma.sub('%s,%s' % (ws['_,'], ws[',_']), value)
    value = re_format_assign.sub('%s=%s' % (ws['_='], ws['=_']), value)
    value = re_format_type_sep.sub('%s->%s' % (ws['_->'], ws['->_']), value)
    value = re_format_semicolon.sub('%s;' % ws['_;'], value)

    return value


def get_context(view):
    ctx = {}
    ctx['view'] = view

    pos = view.sel()[0].begin()
    ctx['scope'] = view.scope_name(pos)

    word = get_context_word(view)
    if word:
        ctx['word'] = word

    if SCOPE_TYPE in ctx['scope']:
        ctx['type'] = get_context_type(view, ctx['scope'])

    if SCOPE_FUNC in ctx['scope']:
        ctx['function'] = get_context_function(view)

    return ctx


def get_context_function(view):
    ctx = {}

    rgn = find_cur_region(view, SCOPE_FUNC)
    ctx['region'] = rgn
    ctx['name'] = find_regions(view, SCOPE_FUNC_NAME, rgn, True)[0][1]
    ctx['block'] = find_regions(view, SCOPE_FUNC_BLOCK, rgn)[0]

    return ctx


def get_context_type(view, scope):
    ctx = {}

    type_groups = ('abstract', 'class', 'enum', 'interface', 'typedef')
    type_scope = None
    for group in type_groups:
        type_scope = 'meta.type.%s.haxe.2' % group
        if type_scope in scope:
            ctx['group'] = group
            break

    type_rgn = find_cur_region(view, type_scope)

    v_rgns = find_regions(view, SCOPE_VAR, type_rgn)
    vname_rgns = find_regions(view, SCOPE_VAR_NAME, type_rgn)
    f_rgns = find_regions(view, SCOPE_FUNC, type_rgn)
    fname_rgns = find_regions(view, SCOPE_FUNC_NAME, type_rgn)
    s_rgns = find_regions(view, SCOPE_STATIC, type_rgn)

    sv_rgns, v_rgns = filter_regions(v_rgns, s_rgns)
    sf_rgns, f_rgns = filter_regions(f_rgns, s_rgns)

    svname_rgns, vname_rgns = filter_regions(vname_rgns, sv_rgns)
    sfname_rgns, fname_rgns = filter_regions(fname_rgns, sf_rgns)

    ctx['region'] = type_rgn
    ctx['name'] = find_regions(view, SCOPE_TYPE_NAME, type_rgn, True)[0][1]
    ctx['block'] = find_regions(view, SCOPE_TYPE_BLOCK, type_rgn)[0]

    def combine(field_group, field_rgns, field_name_rgns):
        lst = []

        for i in range(0, len(field_rgns)):
            lst.append((
                field_group,
                view.substr(field_name_rgns[i]),
                field_rgns[i]))

        return lst

    ctx[FIELD_VAR] = combine(FIELD_VAR, v_rgns, vname_rgns)
    ctx[FIELD_STATIC_VAR] = combine(FIELD_STATIC_VAR, sv_rgns, svname_rgns)
    ctx[FIELD_FUNC] = combine(FIELD_FUNC, f_rgns, fname_rgns)
    ctx[FIELD_STATIC_FUNC] = combine(FIELD_STATIC_FUNC, sf_rgns, sfname_rgns)

    return ctx


def get_fieldnames(context):
    lst = []

    lst.extend([tup[1] for tup in context['type'][FIELD_VAR]])
    lst.extend([tup[1] for tup in context['type'][FIELD_STATIC_VAR]])
    lst.extend([tup[1] for tup in context['type'][FIELD_FUNC]])
    lst.extend([tup[1] for tup in context['type'][FIELD_STATIC_FUNC]])

    return lst


def get_context_word(view):
    pos = view.sel()[0].begin()
    word_rgn = view.word(pos)
    word = view.substr(word_rgn)
    scope = view.scope_name(word_rgn.begin())

    if not re_word.match(word):
        return None

    ignore_scopes = (
        'comment', 'constant', 'entity', 'keyword', 'storage', 'string')
    for sc in ignore_scopes:
        if sc in scope:
            return None

    return word


def get_indent(view, pos):
    return ''


def get_whitespace_style(view):
    global whitespace_style

    def_style = 'function f(a:T<T>, b:T = null):T->T;'
    s = view.settings().get('haxe_whitespace_style', def_style)

    if whitespace_style is None or whitespace_style['style'] != s:
        whitespace_style = {}
        whitespace_style['style'] = s

        mo = re_whitespace_style.search(s)
        if mo is None:
            mo = re_whitespace_style.search(def_style)

        whitespace_style['_('] = mo.group(1)
        whitespace_style['(_'] = mo.group(2)
        whitespace_style['_:'] = mo.group(3)
        whitespace_style[':_'] = mo.group(4)
        whitespace_style['_<'] = mo.group(5)
        whitespace_style['<_'] = mo.group(6)
        whitespace_style['_>'] = mo.group(7)
        whitespace_style['_,'] = mo.group(8)
        whitespace_style[',_'] = mo.group(9)
        whitespace_style['_='] = mo.group(10)
        whitespace_style['=_'] = mo.group(11)
        whitespace_style['_)'] = mo.group(12)
        whitespace_style['_->'] = mo.group(13)
        whitespace_style['->_'] = mo.group(14)
        whitespace_style['_;'] = mo.group(15)

    return whitespace_style


def is_haxe_scope(view):
    return view.score_selector(0, "source.haxe.2") > 0


def set_pos(view, pos):
    view.sel().clear()
    view.sel().add(sublime.Region(pos, pos))
    view.show_at_center(pos)


class HaxeGenerateCodeEdit(sublime_plugin.TextCommand):

    def run(self, edit, text=None, pos=0):
        if text is None:
            return

        set_pos(self.view, pos)
        new_lines = ''
        for c in text:
            if c == '\n':
                new_lines += c
            else:
                break

        if new_lines:
            self.view.run_command('insert', {"characters": new_lines})
            text = text[len(new_lines):]

        self.view.run_command('insert_snippet', {"contents": text})