class FakeGPIO(object):

        #def __init__(self):
        #        self.x = 1  # set some attribute

        def __getattr__(self, attr):
		try:
			return super(FakeGPIO, self).__getattr__(attr)

		except AttributeError:
			return self.__get_global_handler(attr)

	def __get_global_handler(self, name):
		handler = self.__global_handler
		handler.im_func.func_name = name  # Change the method's name
		return handler


	def __global_handler(self, *args, **kwargs):
		pass

GPIO = FakeGPIO()
