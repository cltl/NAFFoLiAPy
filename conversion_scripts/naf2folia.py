#!/usr/bin/env python
#-*- coding:utf-8 -*-

from __future__ import print_function, unicode_literals, division, absolute_import

import sys
import os
import argparse

import KafNafParserPy as naf
from pynlpl.formats import folia

VERSION = '0.1'


def naf2folia(naffile, docid=None):
    nafparser = naf.KafNafParser(naffile)

    if not docid:
        #derive document ID from filename
        docid = os.path.basename(naffile).split('.')[0]

    foliadoc = folia.Document(id=docid)
    foliadoc.declare(folia.Word, 'undefined')
    foliadoc.declare(folia.Sentence, 'undefined')

    textbody = foliadoc.append(folia.Text)
    #TODO: add raw text to textbody

    prevsent_id = None
    prevpara_id = None
    paragraph = None
    prevword = None
    prev_naf_token = None
    for naf_token in nafparser.get_tokens():
        para_id = naf_token.get_para()
        sent_id = naf_token.get_sent()
        if para_id != prevpara_id:
            if prevpara_id is None:
                #first paragraph, declare for completion's sake
                foliadoc.declare(folia.Paragraph, 'undefined')
            paragraph = textbody.append(folia.Paragraph, id=docid + '.p.' + para_id)
        if sent_id != prevsent_id:
            if paragraph:
                sentence = paragraph.append(folia.Sentence, id=docid + '.s.' + sent_id)
            else:
                sentence = textbody.append(folia.Sentence, id=docid + '.s.' + sent_id)

        token_id = naf_token.get_id()
        if prev_naf_token is not None and int(prev_naf_token.get_offset()) + int(prev_naf_token.get_length()) == int(naf_token.get_offset()):
            prevword.space = False
        word = sentence.append(folia.Word, id=docid + '.w.' + token_id)
        word.append(folia.TextContent, naf_token.get_text(), offset=naf_token.get_offset(), ref=textbody)

        prevword = word
        prev_naf_token = naf_token

        prevpara_id = para_id
        prevsent_id = sent_id

    return foliadoc


def main():
    parser = argparse.ArgumentParser(description="NAF to FoLiA convertor", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('naffile', nargs='?', help='Path to a NAF input document')
    parser.add_argument('foliafile', nargs='?', help='Path to a FoLiA output document')
    parser.add_argument('--id', type=str,help="Document ID for the FoLiA document (will be derived from the filename if not set)", action='store',default="",required=False)
    args = parser.parse_args()
    #args.storeconst, args.dataset, args.num, args.bar
    args = parser.parse_args()

    foliadoc = naf2folia(args.naffile, args.id)
    if args.foliafile:
        foliadoc.save(args.foliafile)
    else:
        print(foliadoc.xmlstring())


if __name__ == '__main__':
    main()



