#!/usr/bin/env python
# -*- coding:utf-8 -*-

from __future__ import print_function, unicode_literals, division, absolute_import

from KafNafParserPy import *
from pynlpl.formats import folia
from collections import defaultdict

import sys
import time

#version of this code
version='0.1'

# FoLiA versions this code has been tested on
tested_versions = ['1.2.0']

#global dictionary that maps folia token ids to NAF term ids
fid2tid = {}

#global dictionaries of found annotators for each layer (to be changed)
text_header = {}
term_header = {}
chunk_header = {}
dep_header = {}
entity_header = {}


def set_public_information(folia_obj, naf_header):
    '''

    :param folia_obj:
    :param naf_header:
    :return:
    '''

    naf_public = Cpublic()
    naf_public.set_publicid(folia_obj.id)

    if 'http' in folia_obj.id:
        naf_public.set_uri(folia_obj.id)
    naf_header.set_publicId(naf_public)


def add_lps_to_header(naf_obj, tooldict, layername):
    '''
    Function that adds lp elements to NAF header based on identified tools in FoLiA
    :param naf_obj: naf object that receives header
    :param tooldict: dictionary of toolname and original data
    :param layername: name of layer to which it should be added
    :return:
    '''

    #conversion only applied if original had annotations
    if len(tooldict) > 0:
        currenttime = time.strftime('%Y-%m-%dT%H:%M:%S%Z')
        lp = Clp(name='NAFFoLiAPy/folia2naf.py', version=version, btimestamp=currenttime, timestamp=currenttime)
        naf_obj.add_linguistic_processor(layername, lp)
        for toolname, timestamp in tooldict.items():
            if timestamp is not None:
                original_time = timestamp.strftime('%Y-%m-%dT%H:%M:%S%Z')
            else:
                original_time = 'unknown'
            lp = Clp(name=toolname, timestamp=original_time, btimestamp=original_time, etimestamp=original_time, hostname='unknown')
            naf_obj.add_linguistic_processor(layername, lp)

def create_processes_header(naf_obj):
    '''
    Function that adds all processors to NAF header
    :return: None
    '''
    global text_header, term_header, entity_header, chunk_header, dep_header

    add_lps_to_header(naf_obj, text_header, 'text')
    add_lps_to_header(naf_obj, term_header, 'terms')
    add_lps_to_header(naf_obj, dep_header, 'deps')
    add_lps_to_header(naf_obj, chunk_header, 'chunks')
    add_lps_to_header(naf_obj, entity_header, 'entities')


def header_to_header_layer(folia_obj, naf_obj):
    '''
    :param foliaobj:
    :param nafobj:
    :return:
    '''
    naf_header = CHeader()
    set_public_information(folia_obj, naf_header)
    naf_obj.set_header(naf_header)
    create_processes_header(naf_obj)

    # TODO: add annotation information (as linguistic processes)


def set_word_info(nafWord, word, offset):
    '''
    Adds all information that is deducted from the word form to the new token
    :param nafWord: Cwf() object for new NAF token
    :param word: FoLiA token
    :param offset: offset of word
    :return: offset updated with word length and space if applicable
    '''

    nafWord.set_offset(str(offset))
    text = word.text()
    wLength = len(text)
    nafWord.set_length(str(wLength))
    nafWord.set_text(text)
    offset += wLength
    if word.space:
        offset += 1

    return offset


def create_span(idList):
    '''
    Creates NAF span object pointing to ids in list
    :param idList: list of ids
    :return: span object
    '''
    my_span = Cspan()
    my_span.create_from_ids(idList)

    return my_span


def create_span_from_folia_words(folia_word_list):
    '''
    Goes through list of folia words and identifies corresponding term id for each
    :param folia_word_list: list of FoLiA word objects
    :return: list of term ids
    '''

    global fid2tid
    naf_span = []
    for word in folia_word_list:
        naf_term_id = fid2tid.get(word.id)
        naf_span.append(naf_term_id)
    return naf_span


def add_span_to_elem(naf_elem, span_ids):
    '''
    Creates a NAF span object from a list of ids and adds this to the naf element
    :param naf_elem: a naf element
    :param span_ids: a list of ids that composes the span
    :return: None
    '''
    span = create_span(span_ids)
    naf_elem.set_span(span)



def set_folia_info(folia_word, term):
    '''
    Retrieves information from folia_word and adds this to term
    :param folia_word: folia word object
    :param term: naf term object
    :return: None
    '''
    global term_header

    term.set_morphofeat(folia_word.pos())
    term.set_lemma(folia_word.lemma())
    if not folia_word.annotation(folia.PosAnnotation).annotator in term_header:
        term_header[folia_word.annotation(folia.PosAnnotation).annotator] = folia_word.annotation(folia.PosAnnotation).datetime
    if not folia_word.annotation(folia.LemmaAnnotation).annotator in term_header:
        term_header[folia_word.annotation(folia.LemmaAnnotation).annotator] = folia_word.annotation(folia.LemmaAnnotation).datetime
    #NAF pos tag corresponds to head (attribute's value) of pos element in FoLiA
    #naf_pos = folia_word.xml().find('{http://ilk.uvt.nl/folia}pos').get('head')
    naf_pos = folia_word.annotation(folia.PosAnnotation).feat('head')
    term.set_pos(naf_pos)


def get_and_add_term_information(folia_word, word_count):
    '''
    Retrieves term related information from folia word and adds a term
    :param foliaWord: FoLiA word obj
    :param nafObj: naf object to be updated
    :param word_count: count for term id/span
    :return: None
    '''
    global fid2tid
    naf_term = Cterm()
    # adding obligatory elements
    term_id = 't' + str(word_count)
    naf_term.set_id(term_id)
    fid2tid[folia_word.id] = term_id
    naf_span = create_span(['w' + str(word_count)])
    naf_term.set_span(naf_span)
    # add information from foliaWord
    set_folia_info(folia_word, naf_term)
    return naf_term



def text_to_text_layer(folia_obj, naf_obj):
    '''
    Goes through folia's text and adds all tokens to NAF token layer
    :param folia_obj: folia input object
    :param naf_obj: naf output object
    :return: None
    '''
    global text_header

    offset = 0
    naf_sent = 0
    naf_para = 0
    word_count = 0
    for para in folia_obj.paragraphs():
        naf_para += 1
        for sent in para.sentences():
            sent_nr = str(naf_sent)
            for word in sent.words():
                #for now (we can only capture tool and date any way)
                if not word.annotator in text_header:
                    text_header[word.annotator] = word.datetime
                naf_word = Cwf()
                offset = set_word_info(naf_word, word, offset)
                word_count += 1
                naf_word.set_id('w' + str(word_count))
                naf_word.set_sent(sent_nr)
                naf_word.set_para(str(naf_para))
                naf_obj.add_wf(naf_word)
                naf_term = get_and_add_term_information(word, word_count)
                naf_obj.add_term(naf_term)
            naf_sent += 1

def add_raw_from_text_layer(naf_obj):
    '''
    Goes through NAF's token layer and adds a raw layer based on its data.
    :param naf_obj: nafobject containing text layer
    :return: None
    '''
    raw = ''
    offset = 0
    paragraph = '1'
    for tok in naf_obj.get_tokens():
        # add space and update offset if there was a space
        if tok.get_offset() != str(offset):
            raw += ' '
            offset += 1
        # add double new line for now paragraph
        if tok.get_para() != paragraph:
            raw += '\n\n'
            paragraph = tok.get_para()
        token = tok.get_text()
        raw += token
        offset += len(token)
    naf_obj.set_raw(raw)


def dependencies_to_dependency_layer(folia_obj, naf_obj):
    '''
    Retrieves all dependencies from a folia document, turns them into NAF dep elements and adds them to NAF object
    :param folia_obj: folia object
    :param naf_obj: naf object
    :return: dictionary of (NAF) head id to all its (NAF) dependents ids
    '''
    global dep_header
    head2deps = defaultdict(list)
    for folia_dep in folia_obj.select(folia.Dependency):
        if not folia_dep.annotator in dep_header:
            dep_header[folia_dep.annotator] = folia_dep.datetime
        head_span = create_span_from_folia_words(folia_dep.head().wrefs())
        if len(head_span) > 1:
            print('[WARNING] Unknown situation: head consists of more than one tokens', file=sys.stderr)
        dep_span = create_span_from_folia_words(folia_dep.dependent().wrefs())
        if len(dep_span) > 1:
            print('[WARNING] Situation not captured: dependent consists of more than one token', file=sys.stderr)
        naf_dep = Cdependency()
        naf_head = head_span[0]
        naf_dep.set_from(naf_head)
        n_dep = dep_span[0]
        naf_dep.set_to(n_dep)
        naf_dep.set_function(folia_dep.cls)
        naf_obj.add_dependency(naf_dep)
        head2deps[naf_head].append(n_dep)
    return head2deps


def identify_head_id(span, head2deps):
    '''
    Goes through span and identifies which term is the syntactic head
    :param span: list of term ids
    :param head2deps: list of heads mapped to their dependents
    :return:
    '''
    if len(span) == 1:
        return span[0]
    for term in span:
        if term in head2deps:
            deps = head2deps.get(term)
            if len(set(deps) & set(span)) > 0:
                return term
    print('[WARNING]: no information found to identify head of', span, file=sys.stderr)


def chunking_to_chunks_layer(folia_obj, naf_obj, head2deps):
    '''
    Extract chunks from FoLiA object and add to NAF's chunk layer
    :param folia_obj: folia object
    :param naf_obj: naf object
    :param head2deps: dictionary mapping heads to their dependents
    :return: None
    '''
    global chunk_header
    chunk_id = 1
    for chunk in folia_obj.select(folia.Chunk):
        if not chunk.annotator in chunk_header:
            chunk_header[chunk.annotator] = chunk.datetime
        naf_chunk = Cchunk()
        naf_chunk.set_id('c' + str(chunk_id))
        chunk_id += 1
        naf_span = create_span_from_folia_words(chunk.wrefs())
        add_span_to_elem(naf_chunk, naf_span)
        naf_chunk.set_phrase(chunk.cls)
        chunk_head = identify_head_id(naf_span, head2deps)
        if chunk_head is not None:
            naf_chunk.set_head(chunk_head)
        naf_obj.add_chunk(naf_chunk)


def entities_to_entity_layer(folia_obj, naf_obj):
    '''
    Retrieves all entities from folia obj and adds them to naf entity layer
    :param folia_obj: folia object
    :param naf_obj: naf object
    :return: None
    '''
    global entity_header
    entity_id = 1
    for entity in folia_obj.select(folia.Entity):
        if not entity.annotator in entity_header:
            entity_header[entity.annotator] = entity.datetime
        naf_entity = Centity()
        naf_entity.set_id('e' + str(entity_id))
        entity_id += 1
        naf_span = create_span_from_folia_words(entity.wrefs())
        entity_references = Creferences()
        add_span_to_elem(entity_references, naf_span)
        naf_entity.add_reference(entity_references)
        naf_entity.set_type(entity.cls)
        naf_obj.add_entity(naf_entity)

def check_overall_info(folia_obj):
    '''
    Prints information about possible mismatches and problems in conversion
    :param folia_obj: input file
    :return: None
    '''
    if folia_obj.version is None:
        print('[WARNING] FoLiA input did not have a version indicated.', file=sys.stderr)
    elif not folia_obj.version in tested_versions:
        print('[WARNING] FoLiA version not represented in testset; unknown errors may have occurred.', file=sys.stderr)

    #TODO: create online documentation about missing correspondences; point to them in warnings.


def convert_file_to_naf(inputfolia, outputnaf=None):
    '''
    :param inputfolia: file
    :return: None
    '''

    # if no output name provided, output name is original filename with .naf extension
    if outputnaf == None:
        outputnaf = "".join([inputfolia, '.naf'])

    folia_obj = folia.Document(file=inputfolia)
    check_overall_info(folia_obj)
    # check what information is present and print warnings if not all can be handled (yet)


    naf_obj = KafNafParser(type='NAF')
    if folia_obj.language() is not None:
        naf_obj.set_language(folia_obj.language())
    text_to_text_layer(folia_obj, naf_obj)
    add_raw_from_text_layer(naf_obj)
    head2deps = dependencies_to_dependency_layer(folia_obj, naf_obj)
    chunking_to_chunks_layer(folia_obj, naf_obj, head2deps)
    entities_to_entity_layer(folia_obj, naf_obj)
    header_to_header_layer(folia_obj, naf_obj)
    naf_obj.dump(outputnaf)


def main(argv=None):
    # option to add: keep original identifiers...

    if argv == None:
        argv = sys.argv

    if len(argv) < 2:
        print('python folia2naf.py folia_input.xml (naf_output.xml)')
    elif len(argv) < 3:
        convert_file_to_naf(argv[1])
    else:
        convert_file_to_naf(argv[1], argv[2])


if __name__ == "__main__":
    main()
