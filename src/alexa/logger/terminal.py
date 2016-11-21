#alexa/logger/terminal.py

#$*WHITE
#$WHITE
#$_WHITE
#$-WHITE
#$__WHITE

class DECORATOR():

  def __init__(self, parent, attr_name):
    self.parent = parent
    self.attr_name = attr_name
    self.structure = [attr_name]

  def __call__(self):
    return self.parent._console_out(';'.join(map(str, [self.parent.color_index]))) + self.parent.name + _RESET

  def __getattr__(self, attr):
    if not attr in self.structure:
      self.structure.append(attr)
    return self

  def __str__(self):
    attr_values = []
    for key in self.structure:
      if key in self.parent.attribs:
        if key in _COLORS:
          attr_values.append(self.parent.attribs[key] + 40)
        else:
          attr_values.append(self.parent.attribs[key])
      else:
        raise AttributeError('\'' + key + '\'' + ' attribute does not exist!')

    return self.parent._console_out(';'.join(map(str, [self.parent.color_index] + attr_values)))

class _COLOR_FORMAT(object):
  _DECORATORS = { 'BOLD': 1, 'ITALICS': 3, 'UNDERLINE': 4, 'STRIKETHROUGH': 9 }

  def __init__(self, name, value):
    self.attribs = self._merge(self._DECORATORS, _COLORS)
    self.name = name
    self.value = value
    self.color_index = value + 30

  def __call__(self):
    return self._console_out(';'.join(map(str, [self.color_index]))) + self.name + _RESET

  def __getattr__(self, attr):
    if attr != '_value' and attr != 'color_index':
      return DECORATOR(self, attr)

  def __str__(self):
    return self._console_out(';'.join(map(str, [self.color_index])))

  def _merge(self, x, y):
    new_dict = x.copy()
    new_dict.update(y)
    return new_dict

  def _console_out(self, seq):
    return _ESC_SEQ % seq

_COLORS = {
	'BLACK'         : 0,
	'RED'           : 1,
	'GREEN'         : 2,
	'YELLOW'        : 3,
	'BLUE'          : 4,
	'MAGENTA'       : 5,
	'CYAN'          : 6,
	'WHITE'         : 7,
}

for c, v in _COLORS.iteritems():
	vars()[c] = _COLOR_FORMAT(c, v)

_ESC_SEQ		= "\033[%sm"
_RESET			= "\033[0m"

ESC_SEQS = {
	'ESC_SEQ'	: '\033[',
	'RESET'		: '\033[0m',
}

FORMATS = {
	'BOLD'		: '\033[1m',
	'ITALICS'	: '\033[3m',
	'UNDERLINE'	: '\033[4m',
	'STRIKETHROUGH'	: '\033[9m'
}

COLOR_FORMATS = {
	'BLACK'		: BLACK,
	'RED'		: RED,
	'GREEN'         : GREEN,
	'YELLOW'        : YELLOW,
	'BLUE'          : BLUE,
	'MAGENTA'       : MAGENTA,
	'CYAN'          : CYAN,
	'WHITE'         : WHITE,

	'OK'            : GREEN.BOLD,
	'WARN'          : YELLOW.BOLD,
	'INFO'          : WHITE.BOLD,
	'DEBUG'         : BLUE.BOLD,
	'CRIT'          : YELLOW.BOLD,
	'ERR'           : RED.BOLD,
}

LOG_LEVEL_COLORS = {
	'WARNING'	: YELLOW,
	'INFO'		: BLUE.BOLD,
	'DEBUG'		: WHITE.BOLD.BLUE,
	'CRITICAL'	: RED.BOLD,
	'ERROR'		: WHITE.BOLD.RED
}

globals()['ESC_SEQ'] = type('ESC_SEQS', (object,), ESC_SEQS)
globals()['FORMAT'] = type('FORMATS', (object,), FORMATS)
globals()['COLOR_FORMAT'] = type('COLOR_FORMATS', (object,), COLOR_FORMATS)
