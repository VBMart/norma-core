import unittest
from .scoped_name import ScopedName

class TestScopedName(unittest.TestCase):

    def test_basic_scoped_name(self):
        name = ScopedName("foo")
        self.assertIsNone(name.parent)
        self.assertEqual("foo", name.name)
        self.assertEqual("foo", name.full)

    def test_scoped_name_with_parent(self):
        name = ScopedName("foo.bar")
        self.assertEqual("bar", name.name)
        self.assertEqual("foo.bar", name.full)
        self.assertIsNotNone(name.parent)
        if name.parent is not None:
            self.assertEqual(1, len(name.parent))
            self.assertEqual("foo", name.parent[0])

    def test_scoped_name_operations(self):
        # Test child creation
        parent = ScopedName("foo")
        child_name = parent.child("bar")
        self.assertEqual("foo.bar", child_name.full)

        # Test parent retrieval
        name = ScopedName("foo.bar.baz")
        parent = name.get_parent
        self.assertIsNotNone(parent)
        if parent is not None:
            self.assertEqual("foo.bar", parent.full)

        # Test scope resolution
        name = ScopedName("Message")
        scope = ScopedName("pkg.sub")
        resolved = name.to_scope(scope)
        self.assertEqual("pkg.sub.Message", resolved.full)
        
    def test_equality(self):
        name1 = ScopedName("foo.bar")
        name2 = ScopedName("foo.bar")
        name3 = ScopedName(".foo.bar")
        name4 = ScopedName("foo.baz")

        self.assertEqual(name1, name2)
        self.assertEqual(name1, name3)
        self.assertNotEqual(name1, name4)

    def test_get_parent_root(self):
        name = ScopedName(".foo")
        parent = name.get_parent
        self.assertIsNotNone(parent)
        self.assertEqual(ScopedName('.'), parent)
        
        root_parent = parent.get_parent
        self.assertIsNone(root_parent)

    def test_to_scope_absolute(self):
        name = ScopedName(".Message")
        scope = ScopedName("pkg.sub")
        resolved = name.to_scope(scope)
        self.assertEqual(".Message", resolved.full)
        self.assertNotEqual(resolved, scope)
        
    def test_clone(self):
        name1 = ScopedName("a.b.c")
        name2 = name1.clone()
        self.assertEqual(name1, name2)
        self.assertIsNot(name1, name2)


if __name__ == '__main__':
    unittest.main()