from ftw.testing import MockTestCase
from ftw.upgrade.exceptions import CyclicDependencies
from ftw.upgrade.utils import SizedGenerator
from ftw.upgrade.utils import format_duration
from ftw.upgrade.utils import get_sorted_profile_ids
from ftw.upgrade.utils import topological_sort
from unittest2 import TestCase


class TestTopologicalSort(TestCase):

    def test_simple(self):
        items = ['b', 'a', 'c']
        dependencies = (
            ('a', 'b'),
            ('b', 'c'))

        self.assertEqual(topological_sort(items, dependencies),
                         ['a', 'b', 'c'])

    def test_advanced(self):
        items = ['a', 'c', 'b', 'd']
        dependencies = (
            ('a', 'b'),
            ('a', 'c'),
            ('b', 'd'),
            ('b', 'c'))

        self.assertEqual(topological_sort(items, dependencies),
                         ['a', 'b', 'c', 'd'])

    def test_duplicated(self):
        items = ['a', 'b', 'a']
        dependencies = (
            ('b', 'a'),
            )

        self.assertEqual(topological_sort(items, dependencies),
                         ['b', 'a'])

    def test_cyclic(self):
        items = ['a', 'b']
        dependencies = (
            ('a', 'b'),
            ('b', 'a'))

        self.assertEqual(topological_sort(items, dependencies),
                         None)


class TestSizedGenerator(TestCase):

    def test_length(self):
        generator = SizedGenerator((i for i in range(3)), 3)
        self.assertEqual(len(generator), 3)

    def test_iterating(self):
        generator = SizedGenerator((i for i in range(3)), 3)
        self.assertEqual(list(generator), [0, 1, 2])


class TestSortedProfileIds(MockTestCase):

    def test_dependencies_resolved(self):
        portal_setup = self.mocker.mock()
        self.expect(portal_setup.listProfileInfo()).result([
                {'id': 'baz',
                 'dependencies': [
                        'profile-foo',
                        'profile-bar']},

                {'id': 'foo'},

                {'id': 'bar',
                 'dependencies': ['profile-foo']}]).count(1, 2)

        self.replay()

        self.assertEqual(
            get_sorted_profile_ids(portal_setup),
            ['foo', 'bar', 'baz'])

    def test_cyclic_dependencies(self):
        portal_setup = self.mocker.mock()
        self.expect(portal_setup.listProfileInfo()).result([
                {'id': 'foo',
                 'dependencies': ['profile-bar']},

                {'id': 'bar',
                 'dependencies': ['profile-foo']}]).count(1, 2)

        self.replay()

        with self.assertRaises(CyclicDependencies) as cm:
            get_sorted_profile_ids(portal_setup)

        self.assertEqual(cm.exception.dependencies,
                         [('foo', 'bar'), ('bar', 'foo')])


class TestFormatDuration(TestCase):

    def test_zero_seconds_is_supported(self):
        self.assertEqual('0 seconds', format_duration(0))

    def test_single_second_is_singular(self):
        self.assertEqual('1 second', format_duration(1))

    def test_multiple_seconds_is_plural(self):
        self.assertEqual('2 seconds', format_duration(2))

    def test_single_minute_is_singular(self):
        self.assertEqual(['1 minute',
                          '1 minute, 1 second',
                          '1 minute, 2 seconds'],

                         [format_duration(60),
                          format_duration(60 + 1),
                          format_duration(60 + 2)])

    def test_multiple_minutes_is_plural(self):
        self.assertEqual(['2 minutes, 1 second',
                          '2 minutes, 2 seconds'],

                         [format_duration((2 * 60) + 1),
                          format_duration((2 * 60) + 2)])

    def test_single_hour_is_singular(self):
        self.assertEqual(['1 hour',
                          '1 hour, 1 minute',
                          '1 hour, 2 minutes, 1 second',
                          '1 hour, 2 minutes, 2 seconds'],

                         [format_duration((60 * 60)),
                          format_duration((60 * 60) + 60),
                          format_duration((60 * 60) + (2 * 60) + 1),
                          format_duration((60 * 60) + (2 * 60) + 2)])

    def test_multiple_hours_is_plural(self):
        self.assertEqual(['2 hours',
                          '2 hours, 1 minute',
                          '2 hours, 2 minutes, 1 second',
                          '2 hours, 2 minutes, 2 seconds'],

                         [format_duration((2 * 60 * 60)),
                          format_duration((2 * 60 * 60) + 60),
                          format_duration((2 * 60 * 60) + (2 * 60) + 1),
                          format_duration((2 * 60 * 60) + (2 * 60) + 2)])

    def test_floating_point_seconds_are_ceiled(self):
        self.assertEqual(['1 second',
                          '1 second',
                          '2 seconds',
                          '2 seconds'],

                         [format_duration(0.1),
                          format_duration(0.9),
                          format_duration(1.1),
                          format_duration(1.9)])
