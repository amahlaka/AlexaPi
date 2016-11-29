class Enum():
	def __init__(self, values=False):
		if values:
			for k, v in values.iteritems():
				cls = self.__class__()
				setattr(cls, '_name', k)
				setattr(cls, '_value', v)
				setattr(self.__class__, k, cls)

        def __str__(self):
                n = self._name or ('FIXME_(%r)' % (self._value,))
                return '.'.join((self.__class__.__name__, n))

        def __hash__(self):
                return self.value

        def __repr__(self):
                return '.'.join((self.__class__.__module__, self.__str__()))

        def __eq__(self, other):
                return ((self._value == other._value) or (isinstance(other, (int, long)) and self._value == other))

        def __ne__(self, other):
                return not self.__eq__(other)
