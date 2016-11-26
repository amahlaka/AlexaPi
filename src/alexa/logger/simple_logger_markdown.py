import re
import types

from alexa.logger.terminal import *


class Markdown:
	_BLACK, _RED, _GREEN, _YELLOW, _BLUE, _MAGENTA, _CYAN, _WHITE = range(8)

	_FORMATS = {
		'BOLD': 1,
		'ITALICS': 3,
		'UNDERLINE': 4,
		'REVERSE': 7,
		'STRIKETHROUGH': 9
	}

	_COLORS = {
		'BLACK': _BLACK,
		'RED': _RED,
		'GREEN': _GREEN,
		'YELLOW': _YELLOW,
		'BLUE': _BLUE,
		'MAGENTA': _MAGENTA,
		'CYAN': _CYAN,
		'WHITE': _WHITE
	}

	_CUSTOM = {
		'ok'		: '{{green}}**%s**{{green}}',
		'failed'	: '{{red}}**%s**{{red}}'
	}

	class _ESC:
		SEQ = '\033[%sm'
		RESET = '\033[0m'


	LOG_LEVEL_COLORS = {
		'WARNING'       : '{{yellow}}%s{{yellow}}',
		'INFO'          : '**{{blue}}%s{{blue}}**',
		'DEBUG'         : '**{{white}}%s{{white}}**', #TODO: need to add background color
		'CRITICAL'      : '**{{red}}%s{{red}}**',
		'ERROR'         : '**{{white}}%s{{white}}**' #TODO: need to add background color
	}

	class LogFunctions:
		LOG_START = '{{logstart}}'
		BLANK = '{{blank}}'

		def log_start(self, logger):
			logger.info(self.LOG_START)

		def log_blank_line(self, logger):
			logger.info(self.BLANK)

	class Formatter:
		FORMAT = ("%(asctime)s - [**%(name)-30s**][%(levelname)-20s]" " %(message)s " "(**%(filename)s**:%(lineno)d)")

		def __init__(self, use_color=False):
			self._use_color = use_color
			self._fmt_modified = False
			self._parser = Markdown.Parser()
			self.log_format = self._initialize_log_format()

		def _initialize_log_format(self):
			return self._parser(self.FORMAT, not self._use_color)

		def format(self, record, fmt):
			if self._fmt_modified:
				fmt = self._initialize_log_format()
				self._fmt_cleared = False

			levelname = record.levelname
			msg = record.msg

			# colorize and format logname
			if self._use_color and levelname in Markdown.LOG_LEVEL_COLORS:
				record.levelname = self._parser(Markdown.LOG_LEVEL_COLORS[levelname] % levelname)

			# colorize and format message...if msg is a str
			if isinstance(msg, basestring):
				if msg.find(Markdown.LogFunctions.BLANK) > -1:
					fmt = ''
					self._fmt_modified = True

				elif msg.find(Markdown.LogFunctions.LOG_START) > -1:
					fmt = '%(message)s'
					msg =           '\n\n ##########################################################\n' + \
							'##                                                        ##\n' + \
							'##               {{failed}}ALEXA LOGGING STARTING...{{failed}}                ##\n' + \
							'##                                                        ##\n' + \
							' ##########################################################\n\n\n\n'
					self._fmt_modified = True

				if self._use_color:
					# parse colors/formats TODO: fix BG
					msg = self._parser(msg)
				else:
					msg = self._parser(msg, True)

				record.msg = msg

			return record, fmt


	class _Renderer:
		def __init__(self, colors, formats):
			self.colors = colors
			self.formats = formats

		def __call__(self, structure, text_only=False):
			self.output = []
			for output in structure:
				attr_values = []

				for attribute in output['attributes']:
					if attribute in self.colors:
						attr_values.append(Markdown._COLORS[attribute.upper()] + 30)

					elif attribute in self.formats:
						attr_values.append(Markdown._FORMATS[attribute.upper()])

					else:
						attr_values.append(None)

				if not text_only:
					self.output.append({'seq': ';'.join(map(str, attr_values)), 'text': output['text']})
				else:
					self.output.append({'seq': '', 'text': output['text']})

			return self._render(self.output)

		def _render(self, raw_out):
			out = ''
			for x in raw_out:
				if x['seq'] == None:
					out += x['text']
				else:
					out += '%s%s%s' % (Markdown._ESC.SEQ % x['seq'], x['text'], Markdown._ESC.RESET)

			return out


	class Parser:
		colors = ['black', 'red', 'yellow', 'green', 'blue', 'cyan', 'magenta', 'white']
		formats = ['bold', 'italics', 'reverse', 'underline', 'strikethrough']

		text = re.compile(r'^[\s\S]+?(?=[\\\[_*`~{]| {2,}\n|$)')
		reverse = re.compile(r'^(`+)\s*([\s\S]*?[^`])\s*\1(?!`)')  # `reverse`
		italics = re.compile(r'^\*((?:\*\*|[^\*])+?)\*(?!\*)')  # *italics*
		# italics         = re.compile(r'^\/{2}([\s\S]+?)\/{2}(?!\/)') # //italics//
		bold = re.compile(r'^\*{2}([\s\S]+?)\*{2}(?!\*)')  # **bold**
		underline = re.compile(r'^_{2}([\s\S]+?)_{2}(?!_)')  # __underline__
		strikethrough = re.compile( r'^\~{2}(?=\S)([\s\S]*?\S)\~{2}')  # ~~strikethrough~~

		def __init__(self):
			self.rules = self._merge_array(self.formats, self.colors)

			for key, value in Markdown._CUSTOM.iteritems():
				setattr(self, key, self._custom_compile)

			for color in self.colors:
				setattr(self, color, self._color_compile)

			self.render = Markdown._Renderer(self.colors, self.formats)

		def __call__(self, text, text_only=False):
			self.output = []
			self.parsing = []
			out = self._parse(text)
			return self.render(out, text_only)

		def _merge_array(self, rules_list, color_list):
			rules_list.extend(color_list)
			rules_list.append('text')
			return rules_list

		def _custom_compile(self, custom):
			return re.compile(r'{{%s}}([\s\S]+?){{%s}}' % (custom, custom))

		def _color_compile(self, color):
			return re.compile(r'^{{%s}}([\s\S]+?){{%s}}' % (color, color))

		def _parse(self, text, levels=0, parsing=False):

			def parse(text, levels):
				for key in self.rules:
					if key in self.colors:
						pattern = getattr(self, key)(key)

					else:
						pattern = getattr(self, key)

					m = pattern.match(text)

					if m is not None:
						if not parsing:
							self.parsing = []

						if pattern.groups > 0:
							levels += 1
							self.parsing.append(key)
							self._parse(m.group(1), levels, key)

						else:
							#print {'attributes': list(self.parsing), 'text': m.group(0)}
							self.output.append({'attributes': self.parsing, 'text': m.group(0)})

						return key, m

					else:
						continue

				return False

			while text:
				for k,v in Markdown._CUSTOM.iteritems():
					pattern = getattr(self, k)(k)
					m = pattern.match(text)
					if m is not None:
						text = v % m.group(1) + text[len(m.group(0)):]

				ret = parse(text, levels)

				if ret is not False:
					key, m = ret
					text = text[len(m.group(0)):]
					self.parsing = [parsing]
					continue

				if text:
					raise RuntimeError(
						'Infinite loop at: %s' % text)  # catch parsing error

			return self.output

	def log_hooks(log):
		setattr(log, 'start', types.MethodType(Markdown.LogFunctions().log_start, log))
		setattr(log, 'blank_line', types.MethodType(Markdown().LogFunctions.log_blank_line, log))

	log_hooks = staticmethod(log_hooks)
