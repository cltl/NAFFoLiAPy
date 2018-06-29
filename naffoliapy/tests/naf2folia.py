#!/usr/bin/env python3

import os
import unittest
import KafNafParserPy as naf
from naffoliapy.naf2folia import naf2folia
from pynlpl.formats import folia

EXAMPLE_PATH = os.path.join(os.path.split(__file__)[0], "../../examples/")


nafdoc = naf.KafNafParser(os.path.join(EXAMPLE_PATH,"100911_Northrop_Grumman_and_Airbus_parent_EADS_defeat_Boeing.naf.xml"))
docid = "boeing"
foliadoc = naf2folia(nafdoc, docid)

class NAF2FoLiA_SanityTest(unittest.TestCase):
    def setUp(self):
        self.doc = foliadoc #reusing the same object for speed, so treat as strictly read-only

    def test002_sanity(self):
        """Sanity Check - Testing if result is a proper FoLiA document"""
        self.assertTrue( isinstance(self.doc, folia.Document) )
        self.assertEqual( self.doc.id, docid)

    def test002_tokencheck(self):
        """Sanity Check - Testing full token equality"""
        naf_tokens = list(nafdoc.get_tokens())
        folia_tokens = list(foliadoc.words())
        self.assertTrue( len(naf_tokens) > 0 )
        self.assertEqual( len(naf_tokens), len(folia_tokens) )
        for naf_token, folia_token in zip(naf_tokens, folia_tokens):
            self.assertEqual( docid + '.' + naf_token.get_id() , folia_token.id )
            self.assertEqual( naf_token.get_text(), folia_token.text() )


if __name__ == '__main__':
    unittest.main()
