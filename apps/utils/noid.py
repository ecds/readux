'''
The `NOID <https://confluence.ucop.edu/display/Curation/NOID>`_
(Nice Opaque Identifier) minting logic here uses an unbounded NOID minter
with "extended digits" (:attr:`ALPHABET`) with a check character at the end.

For comparison, you can install the `Ruby <https://github.com/microservices/noid>`_
or `Perl <http://search.cpan.org/dist/Noid/lib/Noid.pm>`_ NOID
implementations and create a new minter comparable to the one implemented
here with this command::

    noid dbcreate .zeeeek

Similarly, noids implemented through this application can be validated
using::

    noid validate- pzc8v

'''

# Historical note:
# This noid minting logic was originally implemented for Emory Library's PID
# Manager https://github.com/emory-libraries/pidman/blob/1.0.3/pidman/pid/noid.py.
# That implementations was based on the Noid.pm Perl module by John Kunze.
# They began using the original Perl code for generating
# NOIDs, but in re-examining how they used the utility they realized they didn't
# really use most of its functionality at all. By the time they realized this
# they were calling into the Perl code from within a Postgres database
# underneath this Django application. they decided to remove a few layers of
# dependencies by re-implementing the tiny bit of NOID-generation logic we
# actually used in Python for direct access from Django.

#: NOID alphabet; specifies the characters to be used for minting noids
ALPHABET = '0123456789bcdfghjkmnpqrstvwxz'
ALPHASIZE = len(ALPHABET)


def _digits(num):
    '''Represent num in base ALPHASIZE. Return an array of digits, most
    significant first.'''
    if not num:
        return []
    arr = []
    while num:
        digit = num % ALPHASIZE
        num = num // ALPHASIZE
        arr.append(digit)
    arr.reverse()
    return arr


def _checksum(digits):
    '''Custom per-digit checksum algorithm originally implemented in Noid.pm
    and duplicated here for compatibility'''
    sum = 0
    pos = 1
    for digit in digits:
        sum += pos * digit
        pos += 1
    return sum % ALPHASIZE


def encode_noid(num):
    '''Encode an integer as a NOID string, including final checksum
    character.'''
    digits = _digits(num)
    digits.append(_checksum(digits))
    return ''.join([ALPHABET[digit] for digit in digits])


def decode_noid(noid):
    '''Decode the integer represented by a NOID string, ignoring the final
    checksum character.'''
    noid = noid[:-1]  # strip checksum character
    power = len(noid) - 1
    num = 0
    for char in noid:
        num += ALPHABET.index(char) * (ALPHASIZE ** power)
        power -= 1
    return num
