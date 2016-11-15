#alexa/logger/font.py

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
