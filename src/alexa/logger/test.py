#alexa/logger/test.py

class terminal():
	COLOR_ESC_SEQ			= "\033[%dm"
	RESET				= "\033[0m"

	class font:
		class style:
			BOLD			= "\033[1m"
			ITALICS			= "\033[3m"
			UNDERLINE		= "\033[4m"
			STRIKETHROUGH		= "\033[9m"


	class color:
		BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

		COLORS = {
			'OK'		: GREEN,
			'WARN'		: YELLOW,
			'INFO'		: WHITE,
			'DEBUG'		: BLUE,
			'CRIT'		: YELLOW,
			'ERR'		: RED,

			'BLACK'		: BLACK,
			'RED'		: RED,
			'GREEN'		: GREEN,
			'YELLOW'	: YELLOW,
			'BLUE'		: BLUE,
			'MAGENTA'	: MAGENTA,
			'CYAN'		: CYAN,
			'WHITE'		: WHITE,
		}

		LOG_LEVEL_COLORS = {
			'WARNING'	: YELLOW,
			'INFO'		: WHITE,
			'DEBUG'		: BLUE,
			'CRITICAL'	: YELLOW,
			'ERROR'		: RED
		}

	def __init__(self):
		pass

	def get_levelname_format(self, levelname):
		if levelname in terminal.color.LOG_LEVEL_COLORS:
			fore_color = 30 + terminal.color.LOG_LEVEL_COLORS[levelname]
			levelname_color = terminal.COLOR_ESC_SEQ % fore_color + levelname + terminal.RESET
			return levelname_color

		return levelname

	def hilite(self, string, status, bold):
		attr = []
		if(sys.stdout.isatty()):
			if status=='g':
				# green
				attr.append('32')
			elif status=='r':
				# red
				attr.append('31')
			elif status=='y':
				# yellow
				attr.append('33')
			elif status=='b':
				# blue
				attr.append('34')
			elif status=='m':
				# magenta
				attr.append('35')
			if bold:
				attr.append('1')

			return '\x1b[%sm%s\x1b[0m' % (';'.join(attr), string)

		else:
			return(string)
