#alexa/logger/colors.py

class color:
	BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

	COLORS = {
		'OK'       : GREEN,
		'WARNING'  : YELLOW,
		'INFO'     : WHITE,
		'DEBUG'    : BLUE,
		'CRITICAL' : YELLOW,
		'ERROR'    : RED,
		'BLACK'    : BLACK,
		'RED'      : RED,
		'GREEN'    : GREEN,
		'YELLOW'   : YELLOW,
		'BLUE'     : BLUE,
		'MAGENTA'  : MAGENTA,
		'CYAN'     : CYAN,
		'WHITE'    : WHITE,
	}

	RESET = "\033[0m"
	COLOR = "\033[1;%dm"
	BOLD = "\033[1m"

	LOG_LEVEL_COLORS = {
		'WARNING': YELLOW,
		'INFO': WHITE,
		'DEBUG': BLUE,
		'CRITICAL': YELLOW,
		'ERROR': RED
	}
