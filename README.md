# NAFFoLiA

Python library and command-line tools for converting between FoLiA and NAF.

## Features

### NAF to FoLiA

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

Anything not listed is not yet supported.

### FoLiA to NAF


