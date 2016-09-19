NAFFoLiA
============

Python library and command-line tools for converting between FoLiA and NAF.

Installation
-----------------

To clone this repository and install, do:


* ``$ git clone https://github.com/cltl/NAFFoLiAPy.git``
* ``$ cd NAFFoLiAPy``
* ``$ python3 install setup.py``


You may want to use ``python2`` for Python 2.7 and you may need to include ``sudo``
if you want to install the package globally. We recommend using a Python
``virtualenv`` though. Create and activate one as follows prior to executing
the above steps:

* ``$ virtualenv --python=python3 naffoliaenv``
* ``$ . naffoliaenv/bin/activate``

Alternatively, use a python distribution like Anaconda.

NAF to FoLiA
----------------

The following conversions are currently supported:

* Raw text
* Token and terms 
  * No support yet for multi-token terms!
  * Offset information is preserved in the conversion
* Part-of-Speech
  * NAF's morphosyntactic feature (``morphofeat``) is converted as a second type of part-of-speech
* Lemmas
* Lexical semantic senses (wordnet external references in NAF)
* Named Entities
* Co-references and events as co-references
* Chunks

Anything not listed is not yet supported.

FoLiA to NAF
-----------------

The following conversions are currently supported:

* Raw text (created from tokens)
* Words to text and terms
   * NAF's possibility of capturing multi-tokens not taken into account
   * offset and length are derived from string and space information
 * Part-of-speech:
   * taken from pos element: NAF's morphofeat = FoLiA's pos class, NAF's pos = FoLiA's pos head
 * Lemmas
 * Chunks
 * Entities
 * Dependencies
  
Anything not listed is not yet supported

