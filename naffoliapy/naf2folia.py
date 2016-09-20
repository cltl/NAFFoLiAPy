#!/usr/bin/env python
#-*- coding:utf-8 -*-

# NAF2FoLiA Convertor
# by Maarten van Gompel, Radboud University Nijmegen
# Licensed under GPLv3

from __future__ import print_function, unicode_literals, division, absolute_import

import sys
import os
import argparse
from collections import defaultdict

import KafNafParserPy as naf
from pynlpl.formats import folia

VERSION = '0.1'


def convert_text_layer(nafparser, foliadoc):
    textbody = foliadoc.append(folia.Text(foliadoc, id=foliadoc.id+'.text'))
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
            paragraph = textbody.append(folia.Paragraph, id=foliadoc.id+ '.para' + para_id)
        if sent_id != prevsent_id:
            if paragraph:
                sentence = paragraph.append(folia.Sentence, id=foliadoc.id+ '.sent' + sent_id)
            else:
                sentence = textbody.append(folia.Sentence, id=foliadoc.id+ '.sent' + sent_id)

        token_id = naf_token.get_id()
        if prev_naf_token is not None and int(prev_naf_token.get_offset()) + int(prev_naf_token.get_length()) == int(naf_token.get_offset()):
            prevword.space = False
        word = sentence.append(folia.Word, id=foliadoc.id+ '.' + token_id)
        offset=int(naf_token.get_offset())
        try:
            offset_valid = naf_raw[offset+int(naf_token.get_length())] == naf_token.get_text()
        except IndexError:
            offset_valid = False
        if not offset_valid:
            print("WARNING: NAF error: offset for token " + token_id +" does not align properly with raw layer! Discarding offset information for FoLiA conversion",file=sys.stderr)
            word.append(folia.TextContent, naf_token.get_text())
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

def unsupported_notice(collection, annotationtitle):
    if collection is not None and list(collection):
        print("WARNING: The following annotation type in NAF can not be converted to FoLiA yet: " +  annotationtitle,file=sys.stderr)

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
        senseset = "https://raw.githubusercontent.com/proycon/folia/master/setdefinitions/" + resource.replace(' ','_') + ".foliaset.xml"
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

def convert_sentiment(naf_term, word):
    unsupported_notice(naf_term.get_sentiment(), "Sentiment")

def convert_terms(nafparser, foliadoc):
    pos_declared = pos2_declared = lemma_declared = False
    for naf_term in nafparser.get_terms():
        span = [ foliadoc.id + '.' + w_id for w_id in naf_term.get_span().get_span_ids() ]
        if len(span) > 1:
            #NAF term spans multiple tokens
            print("WARNING: Convertor limitation: NAF term " + naf_term.get_id() + " spans multiple tokens. Conversion not supported yet!" ,file=sys.stderr)
        else:
            word = foliadoc.index[span[0]]

            naf_pos = naf_term.get_pos()
            if naf_pos:
                if not pos_declared:
                    foliadoc.declare(folia.PosAnnotation, "https://raw.githubusercontent.com/proycon/folia/master/setdefinitions/naf_pos.foliaset.xml")
                    pos_declared = True
                word.append(folia.PosAnnotation, cls=naf_pos, set="https://raw.githubusercontent.com/proycon/folia/master/setdefinitions/naf_pos.foliaset.xml")

            naf_morphofeat = naf_term.get_morphofeat()
            if naf_morphofeat:
                if not pos2_declared:
                    foliadoc.declare(folia.PosAnnotation, "https://raw.githubusercontent.com/proycon/folia/master/setdefinitions/naf_morphofeat.foliaset.xml")
                    pos2_declared = True
                word.append(folia.PosAnnotation, cls=naf_morphofeat, set="https://raw.githubusercontent.com/proycon/folia/master/setdefinitions/naf_morphofeat.foliaset.xml")

            naf_lemma = naf_term.get_lemma()
            if naf_lemma:
                if not lemma_declared:
                    foliadoc.declare(folia.LemmaAnnotation, "https://raw.githubusercontent.com/proycon/folia/master/setdefinitions/naf_lemma.foliaset.xml")
                    lemma_declared = True
                word.append(folia.LemmaAnnotation, cls=naf_lemma)

            convert_senses(naf_term, word)
            convert_sentiment(naf_term, word)

def resolve_span(nafspan, nafparser, foliadoc):
    span = []
    for target in nafspan:
        naf_term = nafparser.get_term(target.get_id())
        span += [ foliadoc[foliadoc.id + '.' + w_id] for w_id in naf_term.get_span().get_span_ids() ]
    return span


def convert_entities(nafparser, foliadoc):
    entityset =  "https://raw.githubusercontent.com/proycon/folia/master/setdefinitions/naf_entities.foliaset.xml"
    first = True
    for naf_entity in nafparser.get_entities():
        if first:
            foliadoc.declare(folia.Entity, entityset)
            first = False
        naf_references = list(naf_entity.get_references())
        if len(naf_references) > 1:
            raise Exception("Entity has multiple references, this was unexpected...",file=sys.stderr)
        span = resolve_span(naf_references[0].get_span(), nafparser, foliadoc)
        sentence = span[0].sentence()
        try:
            layer = sentence.annotation(folia.EntitiesLayer, entityset)
        except folia.NoSuchAnnotation:
            layer = sentence.add(folia.EntitiesLayer, set=entityset)
        layer.add(folia.Entity, *span,  id=foliadoc.id + '.' + naf_entity.get_id(), set=entityset, cls=naf_entity.get_type())

def convert_chunks(nafparser, foliadoc):
    chunkset =  "https://raw.githubusercontent.com/proycon/folia/master/setdefinitions/naf_entities.foliaset.xml"
    first = True
    for naf_chunk in nafparser.get_chunks():
        if first:
            foliadoc.declare(folia.Chunk, chunkset)
            first = False
        span = resolve_span(naf_chunk.get_span(), nafparser, foliadoc)
        sentence = span[0].sentence()
        try:
            layer = sentence.annotation(folia.ChunkingLayer, chunkset)
        except folia.NoSuchAnnotation:
            layer = sentence.add(folia.ChunkingLayer, set=chunkset)
        layer.add(folia.Chunk, *span,  id=foliadoc.id + '.' + naf_chunk.get_id(), set=chunkset, cls=naf_chunk.get_type())

def convert_coreferences(nafparser, foliadoc):
    textbody = foliadoc.data[0]
    corefset = {
        'entity': "https://raw.githubusercontent.com/proycon/folia/master/setdefinitions/naf_coreference.foliaset.xml",
        'event': "https://raw.githubusercontent.com/proycon/folia/master/setdefinitions/naf_events.foliaset.xml"
    }
    declared = defaultdict(bool)
    layer = {}
    for naf_coref in nafparser.get_corefs():
        coreftype = naf_coref.get_type()
        if not coreftype: coreftype = 'entity'

        if not declared[coreftype]:
            foliadoc.declare(folia.CoreferenceChain, corefset[coreftype])
            declared[coreftype] = True

        try:
            layer[coreftype] = textbody.annotation(folia.CoreferenceLayer, corefset[coreftype])
        except folia.NoSuchAnnotation:
            layer[coreftype] = textbody.add(folia.CoreferenceLayer, set=corefset[coreftype])

        corefchain = layer[coreftype].add(folia.CoreferenceChain, id=foliadoc.id + '.' + naf_coref.get_id(),  set=corefset[coreftype])
        for naf_span in naf_coref.get_spans():
            span =  []
            for term_id in naf_span.get_span_ids():
                for w_id in nafparser.get_dict_tokens_for_termid(term_id):
                    span.append( foliadoc[foliadoc.id + '.' + w_id])
            corefchain.add(folia.CoreferenceLink, *span)

def convert_semroles(nafparser, foliadoc):
    predicateset = "https://raw.githubusercontent.com/proycon/folia/master/setdefinitions/naf_predicates.foliaset.xml"
    semroleset = "https://raw.githubusercontent.com/proycon/folia/master/setdefinitions/naf_semroles.foliaset.xml"
    declared = False
    for naf_predicate in nafparser.get_predicates():
        span = resolve_span(naf_predicate.get_span(), nafparser, foliadoc)
        sentence = span[0].sentence()

        if not declared:
            foliadoc.declare(folia.SemanticRole, semroleset)
            foliadoc.declare(folia.Predicate, predicateset)
            declared = True

        try:
            layer = sentence.annotation(folia.SemanticRolesLayer, semroleset)
        except folia.NoSuchAnnotation:
            layer = sentence.add(folia.SemanticRolesLayer, set=semroleset)

        predicate_class = naf_predicate.get_uri()
        confidence = validate_confidence(naf_predicate.get_confidence())

        predicate = layer.add(folia.Predicate, *span, id=foliadoc.id + '.' + naf_predicate.get_id(), set=predicateset, cls=predicate_class, confidence=confidence)

        for naf_role in naf_predicate.get_roles():
            semrole_class = naf_role.get_sem_role()
            span = resolve_span(naf_role.get_span(), nafparser, foliadoc)

            predicate.add(folia.SemanticRole, *span,  id=foliadoc.id + '.' + naf_role.get_id(), set=semroleset, cls=semrole_class)
            # - NAF has no support for confidence on semantic roles

def convert_dependencies(nafparser, foliadoc):
    depset = "https://raw.githubusercontent.com/proycon/folia/master/setdefinitions/naf_dependencies.foliaset.xml"
    declared = False
    for naf_dep in nafparser.get_dependencies():
        naf_term = nafparser.get_term(naf_dep.get_from())
        hd_span = [ foliadoc[foliadoc.id + '.' + w_id] for w_id in naf_term.get_span().get_span_ids() ]

        naf_term = nafparser.get_term(naf_dep.get_to())
        dep_span = [ foliadoc[foliadoc.id + '.' + w_id] for w_id in naf_term.get_span().get_span_ids() ]

        sentence = hd_span[0].sentence()
        assert dep_span[0].sentence() == sentence

        if not declared:
            foliadoc.declare(folia.Dependency, depset)
            declared = True

        try:
            layer = sentence.annotation(folia.DependenciesLayer, depset)
        except folia.NoSuchAnnotation:
            layer = sentence.add(folia.DependenciesLayer, set=depset)

        dependency = layer.add(folia.Dependency, set=depset, cls=naf_dep.get_function() )
        dependency.add(folia.Headspan, *hd_span)
        dependency.add(folia.DependencyDependent, *dep_span)
        # - NAF has no support for IDs or confidence on dependencies

def convert_timeexpressions(nafparser, foliadoc):
    unsupported_notice(nafparser.get_timeExpressions(), "Time Expressions")

def convert_temporalrelations(nafparser, foliadoc):
    unsupported_notice(nafparser.get_tlinks(), "Temporal Relations")

def convert_causalrelations(nafparser, foliadoc):
    #Not documented in NAF specification yet
    unsupported_notice(nafparser.get_clinks(), "Causal Relations")

def convert_syntax(nafparser, foliadoc):
    unsupported_notice(nafparser.get_trees(), "Constituency Parse (syntax)")

def convert_factuality(nafparser, foliadoc):
    unsupported_notice(nafparser.get_factvalues(), "Factuality")

def convert_opinions(nafparser, foliadoc):
    unsupported_notice(nafparser.get_opinions(), "Opinions")

def convert_attribution(nafparser, foliadoc):
    #Not supported in KafNafParser yet!!!
    pass


def naf2folia(naffile, docid=None):
    """
    Converts a NAF Document to FoLiA, returns a FoLiA document instance.
    :param naffile: The NAF file to load (str)
    :param docid: the ID for the FoLiA document, will be derived from the filename if not specified (may not always work out) (str)
    :return: a folia.Document instance
    """

    nafparser = naf.KafNafParser(naffile)


    if not docid:
        #derive document ID from filename
        docid = os.path.basename(naffile).split('.')[0]
        try:
            folia.isncname(docid)
        except ValueError:
            print("Document ID can not be extracted from filename (invalid XML NCName), please set --id manually",file=sys.stderr)
            sys.exit(2)

    foliadoc = folia.Document(id=docid)
    foliadoc.declare(folia.Word, 'undefined')
    foliadoc.declare(folia.Sentence, 'undefined')
    foliadoc.metadata['language'] = nafparser.get_language()

    #Convert metadata from nafHeader/fileDesc and nafHeader/public
    naf_header = nafparser.get_header()
    if naf_header.get_publicId(): foliadoc.metadata['publicId'] = naf_header.get_publicId()
    try:
        if naf_header.get_uri(): foliadoc.metadata['source'] = naf_header.get_uri()
    except AttributeError:
        pass

    naf_filedesc = naf_header.get_fileDesc()
    if naf_filedesc is not None:
        if naf_filedesc.get_title(): foliadoc.metadata['title'] = naf_filedesc.get_title()
        if naf_filedesc.get_author(): foliadoc.metadata['author'] = naf_filedesc.get_author()
        if naf_filedesc.get_creationtime(): foliadoc.metadata['creationtime'] = naf_filedesc.get_creationtime()
        if naf_filedesc.get_location(): foliadoc.metadata['location'] = naf_filedesc.get_location()
        if naf_filedesc.get_filename(): foliadoc.metadata['filename'] = naf_filedesc.get_filename()
        if naf_filedesc.get_filetype(): foliadoc.metadata['filetype'] = naf_filedesc.get_filetype()
        if naf_filedesc.get_publisher(): foliadoc.metadata['publisher'] = naf_filedesc.get_publisher()
        if naf_filedesc.get_magazine(): foliadoc.metadata['magazine'] = naf_filedesc.get_magazine()
        if naf_filedesc.get_section(): foliadoc.metadata['section'] = naf_filedesc.get_section()


    convert_text_layer(nafparser,foliadoc)
    convert_terms(nafparser, foliadoc)
    convert_entities(nafparser, foliadoc)
    convert_chunks(nafparser, foliadoc)
    convert_coreferences(nafparser, foliadoc)
    convert_semroles(nafparser, foliadoc)
    convert_dependencies(nafparser, foliadoc)
    convert_timeexpressions(nafparser, foliadoc)
    convert_temporalrelations(nafparser, foliadoc)
    convert_causalrelations(nafparser, foliadoc)
    convert_syntax(nafparser, foliadoc)
    convert_factuality(nafparser, foliadoc)
    convert_opinions(nafparser, foliadoc)
    convert_attribution(nafparser, foliadoc)

    return foliadoc


def main():
    parser = argparse.ArgumentParser(description="NAF to FoLiA convertor", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('naffile', nargs='?', help='Path to a NAF input document')
    parser.add_argument('foliafile', nargs='?', help='Path to a FoLiA output document')
    parser.add_argument('--id', type=str,help="Document ID for the FoLiA document (will be derived from the filename if not set)", action='store',default="",required=False)
    args = parser.parse_args()
    #args.storeconst, args.dataset, args.num, args.bar

    if not args.naffile:
        parser.print_help()
        sys.exit(2)

    foliadoc = naf2folia(args.naffile, args.id)

    if args.foliafile:
        foliadoc.save(args.foliafile)
    else:
        print(foliadoc.xmlstring())


if __name__ == '__main__':
    main()
