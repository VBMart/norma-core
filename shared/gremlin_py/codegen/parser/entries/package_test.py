import unittest
from .buffer import ParserBuffer
from .package import Package
from .scoped_name import ScopedName

class TestPackageParsing(unittest.TestCase):

    def test_basic_package_declaration(self):
        buf = ParserBuffer("package my.package;")
        pkg = Package.parse(buf)
        self.assertIsNotNone(pkg)
        self.assertEqual(0, pkg.start)
        self.assertEqual(19, pkg.end)
        self.assertEqual(ScopedName(".my.package"), pkg.name)

    def test_package_with_extra_whitespace(self):
        buf = ParserBuffer("package  my.package  ;")
        pkg = Package.parse(buf)
        self.assertIsNotNone(pkg)
        self.assertEqual(ScopedName(".my.package"), pkg.name)

    def test_not_a_package_declaration(self):
        buf = ParserBuffer("message Test {}")
        result = Package.parse(buf)
        self.assertIsNone(result)

    def test_deeply_nested_namespace(self):
        buf = ParserBuffer("package com.example.project.submodule;")
        pkg = Package.parse(buf)
        self.assertIsNotNone(pkg)
        self.assertEqual(ScopedName(".com.example.project.submodule"), pkg.name)

if __name__ == '__main__':
    unittest.main()