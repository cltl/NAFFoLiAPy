#!/usr/bin/env python
#-*- coding:utf-8 -*-

from __future__ import print_function, unicode_literals, division, absolute_import

import sys
import os
import argparse
from collections import defaultdict

import KafNafParserPy as naf
from pynlpl.formats import folia

VERSION = '0.1'


def convert_text_layer(nafparser, foliadoc):
    textbody = foliadoc.append(folia.Text)
    naf_raw = nafparser.get_raw()
    textbody.append(folia.TextContent, naf_raw)

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
            paragraph = textbody.append(folia.Paragraph, id=foliadoc.id+ '.p.' + para_id)
        if sent_id != prevsent_id:
            if paragraph:
                sentence = paragraph.append(folia.Sentence, id=foliadoc.id+ '.s.' + sent_id)
            else:
                sentence = textbody.append(folia.Sentence, id=foliadoc.id+ '.s.' + sent_id)

        token_id = naf_token.get_id()
        if prev_naf_token is not None and int(prev_naf_token.get_offset()) + int(prev_naf_token.get_length()) == int(naf_token.get_offset()):
            prevword.space = False
        word = sentence.append(folia.Word, id=foliadoc.id+ '.w.' + token_id)
        offset=int(naf_token.get_offset())
        try:
            offset_valid = naf_raw[offset+int(naf_token.get_length())] == naf_token.get_text()
        except IndexError:
            offset_valid = False
        if not offset_valid:
            print("WARNING: NAF error: offset for token " + token_id +" does not align properly with raw layer! Discarding offset information for FoLiA conversion",file=sys.stderr)
            word.append(folia.TextContent, naf_token.get_text(), ref=textbody)
        else:
            word.append(folia.TextContent, naf_token.get_text(), offset=naf_token.get_offset(), ref=textbody)

        prevword = word
        prev_naf_token = naf_token

        prevpara_id = para_id
        prevsent_id = sent_id
    return textbody

def validate_confidence(confidence):
    if confidence is None:
        return None
    else:
        confidence = float(confidence)
    if confidence < 0:
        print("WARNING: NAF error: confidence  " + str(confidence) + " is not in range! Forcing to 0"  ,file=sys.stderr)
        return 0.0
    if confidence > 1:
        print("WARNING: NAF error: confidence  " + str(confidence) + " is not in range! Forcing to 1"  ,file=sys.stderr)
        return 1.0
    return confidence

def convert_senses(naf_term, word):
    senses = defaultdict(list) #resource => []
    for naf_exref in naf_term.get_external_references():
        resource = naf_exref.get_resource()
        reference = naf_exref.get_reference()
        features = {}
        if resource.lower().find('wordnet') != -1 or resource.startswith('wn'):
            #wordnet
            #see if the ID follows the NAF convention for wordnet
            if len(reference) > 10 and reference[3] == '-' and reference[6] == '-' and reference[-2] == '-':
                features = {'version': reference[4:6], 'language': reference[:3],'pos': reference[-1]}
                reference = reference[7:-2]
                confidence = validate_confidence(naf_exref.get_confidence())
                if confidence is None: confidence = 0 #needed for sorting later
                senses[resource].append( ( confidence, reference, features) )

    for resource, sensedata in senses.items():
        senseset = "https://raw.githubusercontent.com/cltl/NAFFoLiAPy/setdefinitions/" + resource.replace(' ','_') + ".foliaset.xml"
        word.doc.declare(folia.SenseAnnotation, senseset)
        first = True
        for confidence, reference, features in reversed(sorted(sensedata)): #get highest confidence item first, the rest will be alternatives
            if first:
                anchor = word
            else:
                anchor = word.add(folia.Alternative)
            sense = anchor.add(folia.SenseAnnotation, set=senseset, cls=reference, confidence=confidence)
            if features:
                for subset, cls in features.items():
                    sense.add(folia.Feature, subset=subset,cls=cls)
            first = False

def convert_terms(nafparser, foliadoc):
    pos_declared = pos2_declared = lemma_declared = False
    for naf_term in nafparser.get_terms():
        span = [ foliadoc.id + '.w.' + w_id for w_id in naf_term.get_span().get_span_ids() ]
        if len(span) > 1:
            #NAF term spans multiple tokens
            print("WARNING: Convertor limitation: NAF term " + naf_term.get_id() + " spans multiple tokens. Conversion not supported yet!" ,file=sys.stderr)
        else:
            word = foliadoc.index[span[0]]

            naf_pos = naf_term.get_pos()
            if naf_pos:
                if not pos_declared:
                    foliadoc.declare(folia.PosAnnotation, "https://raw.githubusercontent.com/cltl/NAFFoLiAPy/setdefinitions/naf_pos.foliaset.xml")
                    pos_declared = True
                word.append(folia.PosAnnotation, cls=naf_pos, set="https://raw.githubusercontent.com/cltl/NAFFoLiAPy/setdefinitions/naf_pos.foliaset.xml")

            naf_morphofeat = naf_term.get_morphofeat()
            if naf_morphofeat:
                if not pos2_declared:
                    foliadoc.declare(folia.PosAnnotation, "https://raw.githubusercontent.com/cltl/NAFFoLiAPy/setdefinitions/naf_morphofeat.foliaset.xml")
                    pos2_declared = True
                word.append(folia.PosAnnotation, cls=naf_morphofeat, set="https://raw.githubusercontent.com/cltl/NAFFoLiAPy/setdefinitions/naf_morphofeat.foliaset.xml")

            naf_lemma = naf_term.get_lemma()
            if naf_lemma:
                if not lemma_declared:
                    foliadoc.declare(folia.LemmaAnnotation, "https://raw.githubusercontent.com/cltl/NAFFoLiAPy/setdefinitions/naf_lemma.foliaset.xml")
                    lemma_declared = True
                word.append(folia.LemmaAnnotation, cls=naf_lemma)

            convert_senses(naf_term, word)


def convert_entities(nafparser, foliadoc):
    entityset =  "https://raw.githubusercontent.com/cltl/NAFFoLiAPy/setdefinitions/naf_entities.foliaset.xml"
    first = True
    for naf_entity in nafparser.get_entities():
        if first:
            foliadoc.declare(folia.Entity, entityset)
            first = False
        naf_references = list(naf_entity.get_references())
        if len(naf_references) > 1:
            raise Exception("Entity has multiple references, this was unexpected...",file=sys.stderr)
        span = []
        for target in naf_references[0].get_span():
            naf_term = nafparser.get_term(target.get_id())
            span += [ foliadoc[foliadoc.id + '.w.' + w_id] for w_id in naf_term.get_span().get_span_ids() ]
        sentence = span[0].sentence()
        try:
            layer = sentence.annotation(folia.EntitiesLayer, entityset)
        except folia.NoSuchAnnotation:
            layer = sentence.add(folia.EntitiesLayer, set=entityset)
        layer.add(folia.Entity, *span,  id=foliadoc.id + '.e.' + naf_entity.get_id(), set=entityset, cls=naf_entity.get_type())



def naf2folia(naffile, docid=None):
    nafparser = naf.KafNafParser(naffile)

    if not docid:
        #derive document ID from filename
        docid = os.path.basename(naffile).split('.')[0]

    foliadoc = folia.Document(id=docid)
    foliadoc.declare(folia.Word, 'undefined')
    foliadoc.declare(folia.Sentence, 'undefined')
    foliadoc.metadata['language'] = nafparser.get_language()

    textbody = convert_text_layer(nafparser,foliadoc)
    convert_terms(nafparser, foliadoc)
    convert_entities(nafparser, foliadoc)

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



