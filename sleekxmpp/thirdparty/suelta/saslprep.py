from __future__ import unicode_literals

import sys
import stringprep
import unicodedata


def saslprep(text, strict=True):
    """
    Return a processed version of the given string, using the SASLPrep
    profile of stringprep.

    :param text: The string to process, in UTF-8.
    :param strict: If ``True``, prevent the use of unassigned code points.
    """

    if sys.version_info < (3, 0):
        if type(text) == str:
            text = text.decode('us-ascii')

    # Mapping:
    #
    #  -  non-ASCII space characters [StringPrep, C.1.2] that can be
    #     mapped to SPACE (U+0020), and
    #
    #  -  the 'commonly mapped to nothing' characters [StringPrep, B.1]
    #     that can be mapped to nothing.
    buffer = ''
    for char in text:
        if stringprep.in_table_c12(char):
            buffer += ' '
        elif not stringprep.in_table_b1(char):
            buffer += char

    # Normalization using form KC
    text = unicodedata.normalize('NFKC', buffer)

    # Check for bidirectional string
    buffer = ''
    first_is_randal = False
    if text:
        first_is_randal = stringprep.in_table_d1(text[0])
        if first_is_randal and not stringprep.in_table_d1(text[-1]):
            raise UnicodeError('Section 6.3 [end]')

    # Check for prohibited characters
    for x in range(len(text)):
        if strict and stringprep.in_table_a1(text[x]):
            raise UnicodeError('Unassigned Codepoint')
        if stringprep.in_table_c12(text[x]):
            raise UnicodeError('In table C.1.2')
        if stringprep.in_table_c21(text[x]):
            raise UnicodeError('In table C.2.1')
        if stringprep.in_table_c22(text[x]):
            raise UnicodeError('In table C.2.2')
        if stringprep.in_table_c3(text[x]):
            raise UnicodeError('In table C.3')
        if stringprep.in_table_c4(text[x]):
            raise UnicodeError('In table C.4')
        if stringprep.in_table_c5(text[x]):
            raise UnicodeError('In table C.5')
        if stringprep.in_table_c6(text[x]):
            raise UnicodeError('In table C.6')
        if stringprep.in_table_c7(text[x]):
            raise UnicodeError('In table C.7')
        if stringprep.in_table_c8(text[x]):
            raise UnicodeError('In table C.8')
        if stringprep.in_table_c9(text[x]):
            raise UnicodeError('In table C.9')
        if x:
            if first_is_randal and stringprep.in_table_d2(text[x]):
                raise UnicodeError('Section 6.2')
            if not first_is_randal and \
               x != len(text) - 1 and \
               stringprep.in_table_d1(text[x]):
                raise UnicodeError('Section 6.3')

    return text
