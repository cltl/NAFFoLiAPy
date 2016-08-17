#!/usr/bin/env python
#-*- coding:utf-8 -*-

from __future__ import print_function, unicode_literals, division, absolute_import

from KafNafParserPy import *
from pynlpl.formats import folia

import sys


def header_to_header_layer(foliaObj, nafObj):
    '''
    :param foliaobj:
    :param nafobj:
    :return:
    '''
    myPublic = Cpublic()
    myPublic.set_publicid(foliaObj.id)


    if 'http' in foliaObj.id:
        myPublic.set_uri(foliaObj.id)

    myHeader = CHeader()
    myHeader.set_publicId(myPublic)
    nafObj.set_header(myHeader)

    #TODO: add annotation information (as linguistic processes)


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


def text_to_text_layer(foliaObj, nafObj):
    '''
    Goes through folia's text and adds all tokens to NAF token layer
    :param foliaobj: folia input object
    :param nafobj: naf output object
    :return: None
    '''
    #FoLiA does not provide offset, length; setting it ourselves
    #More complex word ids, for now not taken over in NAF; flipping back and forth,
    #i.e. conversion to NAF will generate NAF ids, conversion to FoLiA will generate FoLiA ids
    offset = 0
    naf_sent=0
    naf_para=0
    word_count = 0
    for para in foliaObj.paragraphs():
        naf_para += 1
        for sent in para.sentences():
            sent_nr = str(naf_sent)
            for word in sent.words():
                naf_word = Cwf()
                offset = set_word_info(naf_word, word, offset)
                word_count += 1
                naf_word.set_id('w' + str(word_count))
                naf_word.set_sent(sent_nr)
                naf_word.set_para(str(naf_para))
                nafObj.add_wf(naf_word)
            naf_sent += 1

def text_to_text_layer_bak(foliaObj, nafObj):
    '''
    Goes through folia's text and adds all tokens to NAF token layer
    :param foliaobj: folia input object
    :param nafobj: naf output object
    :return: None
    '''
    #FoLiA does not provide offset, length; setting it ourselves
    #More complex word ids, for now not taken over in NAF; flipping back and forth,
    #i.e. conversion to NAF will generate NAF ids, conversion to FoLiA will generate FoLiA ids
    offset = 0
    naf_sent=0
    word_count = 0
    for sent in foliaObj.sentences():
        sent_nr = str(naf_sent)
        for word in sent.words():
            naf_word = Cwf()
            offset = set_word_info(naf_word, word, offset)
            word_count += 1
            naf_word.set_id('w' + str(word_count))
            naf_word.set_sent(sent_nr)
            nafObj.add_wf(naf_word)
        naf_sent += 1


def add_raw_from_text_layer(nafObj):
    '''
    Goes through NAF's token layer and adds a raw layer based on its data.
    :param nafobj: nafobject containing text layer
    :return: None
    '''
    raw = ''
    offset = 0
    paragraph = '1'
    for tok in nafObj.get_tokens():
        #add space and update offset if there was a space
        if tok.get_offset() != str(offset):
            raw += ' '
            offset += 1
        #add double new line for now paragraph
        if tok.get_para() != paragraph:
            raw += '\n\n'
            paragraph = tok.get_para()
        token = tok.get_text()
        raw += token
        offset += len(token)
    nafObj.set_raw(raw)


def check_overall_info(foliaObj):
    '''
    :param foliaObj:
    :return:
    '''
    if foliaObj.version is None:
        print('[WARNING] FoLiA input did not have a version indicated.', file=sys.stderr)

    #print('Problems')


def convert_file_to_naf(inputfolia, outputnaf=None):
    '''
    :param inputfolia: file
    :return: None
    '''

    #if no output name provided, output name is original filename with .naf extension
    if outputnaf == None:
        outputnaf = "".join([inputfolia, '.naf'])

    foliaObj = folia.Document(file=inputfolia)
    check_overall_info(foliaObj)
    #check what information is present and print warnings if not all can be handled (yet)


    nafObj = KafNafParser(type='NAF')
    text_to_text_layer(foliaObj, nafObj)
    add_raw_from_text_layer(nafObj)
    nafObj.dump(outputnaf)

    header_to_header_layer(foliaObj, nafObj)
    #print(foliaObj.version)


def main(argv=None):


    #option to add: keep original identifiers...
    #option to add: language

    if argv==None:
        argv=sys.argv

    if len(argv) < 2:
        print('python folia2naf.py folia_input.xml (naf_output.xml)')
    elif len(argv) < 3:
        convert_file_to_naf(argv[1])
    else:
        convert_file_to_naf(argv[1], argv[2])



if __name__ == "__main__":
    main()
