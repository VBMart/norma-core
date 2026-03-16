import unittest

from .entries.buffer import ParserBuffer
from .entries.file import ProtoFile
from .entries.scoped_name import ScopedName
from .resolver import find_local_extend_source, resolve_extend, resolve_refs

class ResolverTest(unittest.TestCase):

    def test_local_extend(self):
        buf = ParserBuffer("""
        message A {
          message B {
            extend C {
            }
          }
        
          message C {
          }
        }
        """)
        pf = ProtoFile.parse(buf)
        
        extend = ScopedName("C")
        message_scope = ScopedName(".A.B")
        
        msg = find_local_extend_source(pf, message_scope, extend)
        self.assertIsNotNone(msg)
        self.assertEqual("C", msg.name.name)
        self.assertEqual(".A.C", msg.name.full)

    def test_basic_extend_fields(self):
        buf = ParserBuffer("""
        message A {
          message B {
            extend C {
            }
          }
        
          message C {
            D d = 1;
          }
          message D {
          }
        }
        """)
        pf = ProtoFile.parse(buf)
        
        resolve_extend(pf)
        resolve_refs(pf)
        
        fields = pf.messages[0].messages[0].fields
        self.assertEqual(1, len(fields))
        self.assertEqual("d", fields[0].f_name)

    def test_local_enum_resolve(self):
        buf = ParserBuffer("""
         package a.b.c;
        
         enum E {
           A = 1;
         }
        
         message M {
           E e = 1;
         }
        """)
        pf = ProtoFile.parse(buf)
        resolve_refs(pf)
        
        f = pf.messages[0].fields[0]
        self.assertIsNotNone(f.f_type.ref_local_enum)

    def test_local_msg_reslove(self):
        buf = ParserBuffer("""
         package a.b.c;
        
         message M {
           message N {
           }
         }
        
         message O {
           M.N n = 1;
         }
        """)
        pf = ProtoFile.parse(buf)
        resolve_refs(pf)
        
        f = pf.messages[1].fields[0]
        self.assertIsNotNone(f.f_type.ref_local_message)

    def test_import_enum_resolve(self):
        buf1 = ParserBuffer("""
         package a.b.c;
        
         enum E {
           A = 1;
         }
        """)
        pf1 = ProtoFile.parse(buf1)
        
        buf2 = ParserBuffer("""
         package a.b.c;
        
         import "c.proto";
        
         message M {
           E e = 1;
         }
        """)
        pf2 = ProtoFile.parse(buf2)
        pf2.imports[0].target = pf1
        
        resolve_refs(pf2)
        
        f = pf2.messages[0].fields[0]
        self.assertIsNotNone(f.f_type.ref_external_enum)
        self.assertIsNotNone(f.f_type.ref_import)

    def test_import_enum_package_resolve(self):
        buf1 = ParserBuffer("""
         package p1;
        
         enum E {
           A = 1;
         }
        """)
        pf1 = ProtoFile.parse(buf1)
        
        buf2 = ParserBuffer("""
         package p2;
        
         import "c.proto";
        
         message M {
           p1.E e = 1;
         }
        """)
        pf2 = ProtoFile.parse(buf2)
        pf2.imports[0].target = pf1
        
        resolve_refs(pf2)
        
        f = pf2.messages[0].fields[0]
        self.assertIsNotNone(f.f_type.ref_external_enum)
        self.assertIsNotNone(f.f_type.ref_import)

    def test_import_same_package_resolve(self):
        buf1 = ParserBuffer("""
         package p1.p2;
        
         enum E {
           A = 1;
         }
        """)
        pf1 = ProtoFile.parse(buf1)
        
        buf2 = ParserBuffer("""
         package p1.p2;
        
         import "c.proto";
        
         message M {
           .p1.p2.E e = 1;
         }
        """)
        pf2 = ProtoFile.parse(buf2)
        pf2.imports[0].target = pf1
        
        resolve_refs(pf2)
        
        f = pf2.messages[0].fields[0]
        self.assertIsNotNone(f.f_type.ref_external_enum)
        self.assertIsNotNone(f.f_type.ref_import)

    def test_local_enum_proto2_resolve(self):
        buf = ParserBuffer("""
         syntax = "proto2";
        
         enum GGType {
             gg_generic   = 1;
             gg_other1    = 2;
             gg_other2    = 3;
         }
         message Usage {
            optional GGType     ggtype = 2 [default = gg_generic];
         }
        """)
        pf = ProtoFile.parse(buf)
        resolve_refs(pf)
        
        f = pf.messages[0].fields[0]
        self.assertIsNotNone(f.f_type.ref_local_enum)

if __name__ == '__main__':
    unittest.main()