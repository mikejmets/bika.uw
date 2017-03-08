from bika.uw.testing import BIKA_UW_ROBOT_TESTING
from plone.testing import layered
from pkg_resources import resource_listdir
import robotsuite
import unittest


robots = [f for f in resource_listdir("bika.uw", "tests")
          if f.endswith(".robot")]


def test_suite():
    suite = unittest.TestSuite()
    for robot in robots:
        suite.addTests([
            layered(robotsuite.RobotTestSuite(robot), layer=BIKA_UW_ROBOT_TESTING),
        ])
    return suite
