# run_test.py
import unittest

import test.player as player
import test.logging as logging

# initialize the test suite
loader = unittest.TestLoader()
suite  = unittest.TestSuite()

# add tests to the test suite
suite.addTests(loader.loadTestsFromModule(player))
suite.addTests(loader.loadTestsFromModule(logging))

# initialize a runner, pass it your suite and run it
runner = unittest.TextTestRunner(verbosity=3)
result = runner.run(suite)
