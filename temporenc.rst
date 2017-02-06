=========
Temporenc
=========

comprehensive binary encoding format for dates and times
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Features
========

Flexible
--------

*Temporenc* encodes **any combination of date, time, and time zone offset**
information: year, month, day, hour, minute, second, sub-second precision, and
UTC offset. **Each field is optional.**

Compact
-------

*Temporenc* uses a **compact binary encoding scheme**. Encoded values have a
variable size **between 3 and 10 bytes**. Values of the **same type** always
have the **same size**.

Machine-friendly
----------------

Encoded *temporenc* values are **self-describing**, and can be consumed from a
**stream without framing**. Lexicographically **sorting encoded values** of the
same type puts the values in **chronological order**.


Overview
========

.. class:: lead

*Temporenc* is a comprehensive binary encoding format for dates and times. It
provides a low level building block for higher level protocols and file formats.

*Temporenc* only deals with the encoding of date and time related information,
and is designed for embedding into other encoding schemes. The only requirement
is that embedding formats have support for arbitrary byte strings. This makes
*temporenc* a perfect companion for encoding schemes that encode arbitrary data
structures but lack a flexible date/time type (if any), such as `MessagePack
<http://msgpack.org/>`_, `Protocol Buffers
<https://developers.google.com/protocol-buffers/>`_, and `Thrift
<https://thrift.apache.org/>`_. Due to its compactness and ordering properties,
*temporenc* is also a perfect fit for (partial) keys in key/value stores.

Temporenc is flexible
---------------------

The format is very flexible and supports any combination of a date, a
time, and a time zone offset. Within each of these components, each
field is also optional, e.g. it is possible to encode a year and a
month without a day. Times can have sub-second precision using either
milliseconds, microseconds, or nanoseconds. Time zones use an UTC
offset with 15 minute granularity, allowing any time zone in use in
the world to be represented.

Temporenc is compact
--------------------

*Temporenc* values have a variable size between 3 and 10 bytes,
depending on the components being included. Values of the same type
(and precision) always have the same size. For example, an encoded
date uses 3 bytes, an encoded time also takes 3 bytes, and an encoded
date with time uses 5 bytes. At the other extreme, it takes only 10
bytes to encode a date with time using nanosecond precision and a time
zone offset.

Temporenc is machine-friendly
-----------------------------

*Temporenc* values are self-describing; consuming applications do not need to
know which variant was used for encoding. Since all information needed for
decoding can be derived from the first byte, values can be read from streams
without framing. Encoded values of the same type (and precision) can be sorted
using normal lexicographical sorting routines, i.e. without decoding. Earlier
dates sort first, missing values sort last. This makes *temporenc* values very
suited for use in search trees or as (partial) keys in key/value stores.


Conceptual model
================

*Temporenc* is built around two main concepts: *components* and *types*. This
specification defines four **components**, each representing a single aspect of
the *temporenc* date/time model:

* Component ``D`` (date)

  This component contains year, month, and day information. Each field is
  optional.

* Component ``T`` (time)

  This component contains hour, minute, and second information. Each field is
  optional.

* Component ``S`` (sub-second precision)

  This is a refinement to the time component that allows for a more precise time
  representation, expressed as either milliseconds, microseconds, or
  nanoseconds.

* Component ``Z`` (time zone offset)

  This component specifies the UTC offset.

The above components can be combined to create a complete date/time
value. *Temporenc* defines six **types** for common combinations. Each
type represents a particular combination of date, time, sub-second
time precision, and time zone offset information:

* Type ``D``

  Date only, encoded as 3 bytes.

* Type ``T``

  Time only, encoded as 3 bytes.

* Type ``DT``

  Date + time, encoded as 5 bytes.

* Type ``DTZ``

  Date + time + time zone offset, encoded as 6 bytes.

* Type ``DTS``

  Date + time with sub-second precision, encoded as 6–9 bytes (precision
  dependent).

* Type ``DTSZ``

  Date + time with sub-second precision + time zone offset, encoded as 7–10 bytes
  (precision dependent).


The canonical *type* ``DTSZ`` contains all components, making it a superset of
the other types. Since any component (and each field within) can be left blank,
it can represent all possible combinations of components (dates, times, and so
on). This makes the ``DTSZ`` *type* the most flexible , but also the most
space-consuming.

Applications can use a different *type* to save space, at the cost of reduced
expressiveness. The types are chosen in such a way that both sub-second
precision and time zone support are completely optional. By using the correct
*type* the storage overhead for unused components can be eliminated completely,
since *temporenc* uses a different packing format for each *type*.


Encoding rules
==============

This section describes how the components and types of the *temporenc* model are
encoded into a byte string. Encoding is done in two stages: encoding individual
components, followed by packing the encoded components together to construct the
encoded value as a byte string.


Encoding individual components
------------------------------

In the first stage, each component is encoded separately, resulting in an array
of bits. The rules for encoding components are the same for all *types*. For
representing numbers as bit strings, *temporenc* always uses unsigned big-endian
notation, e.g. encoding the number 13 into 5 bits results in the bit string
``01101`` (8 + 4 + 1).

Date component (``D``)
""""""""""""""""""""""

The date component (``D``) always uses 21 bits, divided in three groups:

* Year (12 bits)

  An integer in the range 0–4094 (both inclusive); the special value 4095 means
  no value is set.

* Month (4 bits)

  An integer in the range 0–11 (both inclusive); the special value 15 means no
  value is set. January is encoded as 0, February as 1, and so on. Note that
  this is off-by-one compared to human month numbering.

* Day (5 bits)

  An integer in the range 0–30 (both inclusive); the special value 31 means no
  value is set. The first day of the month is encoded as 0, the next as 1. Note
  that this is off-by-one compared to human day numbering.

Examples:

================ ========== ================ ========= =========
Format           Value      Year             Month      Day
================ ========== ================ ========= =========
year, month, day 1983-01-15 ``011110111111`` ``0000``  ``01110``
year, month      1983-01    ``011110111111`` ``0000``  ``11111``
year             1983       ``011110111111`` ``1111``  ``11111``
month, day       01-15      ``111111111111`` ``0000``  ``01110``
================ ========== ================ ========= =========


Time component (``T``)
""""""""""""""""""""""

The time component (``T``) always uses 17 bits, divided in three groups:

* Hour (5 bits)

  An integer in the range 0–23 (both inclusive); the special value 31 means no
  value is set.

* Minute (6 bits)

  An integer in the range 0–59 (both inclusive); the special value 63 means no
  value is set.

* Second (6 bits)

  An integer in the range 0–60 (both inclusive); the special value 63 means no
  value is set. Note that the value 60 is supported because it is required to
  correctly represent leap seconds.

Examples:

==================== ======== ========== ========== ==========
Format               Value    Hour       Minute     Second
==================== ======== ========== ========== ==========
hour, minute, second 18:25:12 ``10010``  ``011001`` ``001100``
hour, minute         18:25    ``10010``  ``011001`` ``111111``
==================== ======== ========== ========== ==========


Sub-second precision time component (``S``)
"""""""""""""""""""""""""""""""""""""""""""

The sub-second time precision component (``S``) is expressed as either
milliseconds (ms), microseconds (µs), or nanoseconds (ns). Each precision
requires a different number of bits of storage space. This means that unlike the
other components, this component uses a variable number of bits, indicated by a
2-bit precision tag, referred to as ``P``.

* Milliseconds (10 bits value, 2 bits tag, 12 bits in total)

  An integer in the range 0–999 (both inclusive) represented as 10 bits. The
  precision tag ``P`` is ``00``.

* Microseconds (20 bits value, 2 bits tag, 22 bits in total)

  An integer in the range 0–999999 (both inclusive) represented as 20 bits. The
  precision tag ``P`` is ``01``.

* Nanoseconds (30 bits value, 2 bits tag, 32 bits in total)

  An integer in the range 0–999999999 (both inclusive) represented as 30 bits.
  The precision tag ``P`` is ``10``.

* Empty sub-second precision (0 bits value, 2 bits tag, 2 bits in total)

  The precision tag ``P`` is ``11``, and no additional information is encoded.
  Note that if no sub-second precision time component is required, using a
  *type* that does not include this component at all is more space efficient,
  e.g. ``DTZ`` instead of ``DTSZ``.

Examples:

============ ============ ============= ==================================
Precision    Value        Precision tag ms/µs/ns
============ ============ ============= ==================================
milliseconds 123 ms       ``00``        ``0001111011``
microseconds 123456 µs    ``01``        ``00011110001001000000``
nanoseconds  123456789 ns ``10``        ``000111010110111100110100010101``
none         (not set)    ``11``        (nothing)
============ ============ ============= ==================================


Time zone offset component (``Z``)
""""""""""""""""""""""""""""""""""

The time zone offset component (``Z``) always uses 7 bits.

*Temporenc* uses UTC offsets (usually written as ±HH:MM) to represent time zone
information. The UTC offset is expressed as the number of 15 minute increments
from UTC, with the constant 64 added to it to produce a positive integer, i.e.
``(offset_in_minutes / 15) + 64``. The resulting number must be in the range
0–125 (both inclusive). The special value 127 means no value is set.

The special value 126 means that this value does carry time zone information,
but that it is not expressed as an embedded UTC offset. This makes it possible
to use more elaborate time zone handling with *temporenc* values, for example
using geographical identifiers from the `tzdata
<http://en.wikipedia.org/wiki/Tz_database>`_ project. The actual inclusion of
additional time zone information is outside the scope of *temporenc*;
the value 126 is just an indicator that the value carries a time zone,
but that that information is not present in the value itself.

Examples:

========== ================ ============= =============
Offset     Offset           Encoded value Encoded value
(±hh:mm)   (15m increments) (decimal)     (bits)
========== ================ ============= =============
+00:00     0                64            ``1000000``
+01:00     4                68            ``1000100``
−06:00     −24              40            ``0101000``
========== ================ ============= =============



Packing encoded components
--------------------------

The second encoding stage is about packing the encoded components into the final
byte string. An encoded *temporenc* value is basically a concatenation of the
bit strings for each component. The exact packing format depends on the *type*,
which means each *type* has its own bit packing rules. Each *type* is assigned a
unique *type tag*, which is a short identifying bit string included in the first
byte of the encoded value. The advantages of this approach are:

* Encoded values are self-describing.

* The total size of encoded values is very small.

* Lexicographical sorting of encoded values of the same type (and
  precision) results in the same ordering as the natural text-based
  ordering. This means that mixing values with different UTC offsets
  will sort based on the literal date and time specified, not the
  equivalent instant in UTC.


* A decoder needs only the first byte to determine the total size and layout of
  the complete value, which allows for decoding values from a stream without the
  need for framing (specifying the length).

The table below specifies the *type tag* for each *type*, and the order used for
the concatenation of the encoded components:

======== =========== ===== ===== ===== ===== ===== ==============
Type     Type tag    ``P`` ``D`` ``T`` ``S`` ``Z`` Padding
======== =========== ===== ===== ===== ===== ===== ==============
``D``    ``100``             ✓
``T``    ``1010000``               ✓
``DT``   ``00``              ✓     ✓
``DTZ``  ``110``             ✓     ✓           ✓
``DTS``  ``01``        ✓     ✓     ✓     ✓         ✓ (if needed)
``DTSZ`` ``111``       ✓     ✓     ✓     ✓     ✓   ✓ (if needed)
======== =========== ===== ===== ===== ===== ===== ==============

The general approach for creating the final byte strings, as detailed in the
next subsection, is as follows:

* Start with an empty bit array.

* Concatenate the *type tag*.

* Concatenate each included component, including the sub-second precision tag
  ``P`` (if any).

* Pad the bit array with zeroes to align it to the next multiple of 8, i.e.
  to the next byte boundary (only for *types* with sub-second precision, and
  only if needed).

* Return the bit array as a byte string.

The remainder of this section specifies the exact byte layout for each encoded
*temporenc* type, including examples showing both bit strings and bytes
(hexadecimal notation).

Type ``D`` (date)
"""""""""""""""""

The *type tag* is ``100``. Encoded values use 3 bytes in this format::

  100DDDDD DDDDDDDD DDDDDDDD

Example: *1983-01-15* is encoded as ``10001111 01111110 00001110`` (bits) or
``8f 7e 0e`` (hex bytes).

Type ``T`` (time)
"""""""""""""""""

The *type tag* is ``1010000``. Encoded values use 3 bytes in this format::

  1010000T TTTTTTTT TTTTTTTT

Example: *18:25:12* is encoded as ``10100001 00100110 01001100`` (bits) or ``a1
26 4c`` (hex bytes).

Type ``DT`` (date + time)
"""""""""""""""""""""""""

The *type tag* is ``00``. Encoded values use 5 bytes in this format::

  00DDDDDD DDDDDDDD DDDDDDDT TTTTTTTT
  TTTTTTTT

Example: *1983-01-15T18:25:12* is encoded as ``00011110 11111100 00011101
00100110 01001100`` (bits) or ``1e fc 1d 26 4c`` (hex bytes).

Type ``DTZ`` (date + time + time zone offset)
"""""""""""""""""""""""""""""""""""""""""""""

The *type tag* is ``110``.
Encoded values use 6 bytes in this format::

  110DDDDD DDDDDDDD DDDDDDDD TTTTTTTT
  TTTTTTTT TZZZZZZZ

Example: *1983-01-15T18:25:12+01:00* is encoded as ``11001111 01111110 00001110
10010011 00100110 01000100`` (bits) or ``cf 7e 0e 93 26 44`` (hex bytes).

Type ``DTS`` (date + time with sub-second precision)
""""""""""""""""""""""""""""""""""""""""""""""""""""

The *type tag* is ``01``, followed by the precision tag ``P``.
Values are zero-padded on the right up to the first byte boundary.

* For millisecond (ms) precision, encoded values use 7 bytes in this format::

    01PPDDDD DDDDDDDD DDDDDDDD DTTTTTTT
    TTTTTTTT TTSSSSSS SSSS0000

  Example: *1983-01-15T18:25:12.123* (millisecond precision) is encoded as
  ``01000111 10111111 00000111 01001001 10010011 00000111 10110000`` (bits) or
  ``47 bf 07 49 93 07 b0`` (hex bytes).

* For microsecond (µs) precision, encoded values use 8 bytes in this format::

    01PPDDDD DDDDDDDD DDDDDDDD DTTTTTTT
    TTTTTTTT TTSSSSSS SSSSSSSS SSSSSS00

  Example: *1983-01-15T18:25:12.123456* (microsecond precision) is encoded as
  ``01010111 10111111 00000111 01001001 10010011 00000111 10001001 00000000``
  (bits) or ``57 bf 07 49 93 07 89 00`` (hex bytes).

* For nanosecond (ns) precision, encoded values use 9 bytes in this format::

    01PPDDDD DDDDDDDD DDDDDDDD DTTTTTTT
    TTTTTTTT TTSSSSSS SSSSSSSS SSSSSSSS
    SSSSSSSS

  Example: *1983-01-15T18:25:12.123456789* (nanosecond precision) is encoded as
  ``01100111 10111111 00000111 01001001 10010011 00000111 01011011 11001101
  00010101`` (bits) or ``67 bf 07 49 93 07 5b cd 15`` (hex bytes).

* In case the sub-second precision component has no value, encoded values use 6
  bytes in this format::

    01PPDDDD DDDDDDDD DDDDDDDD DTTTTTTT
    TTTTTTTT TT000000

  Example: *1983-01-15T18:25:12* (no precision) is encoded as ``01110111
  10111111 00000111 01001001 10010011 00000000`` (bits) or ``77 bf 07 49 93 00``
  (hex bytes).

Type ``DTSZ`` (date + time with sub-second precision + time zone offset)
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

The *type tag* is ``111``, followed by the precision tag ``P``.
Values are zero-padded on the right up to the first byte boundary.

TODO: fix example values to have no utc conversion

* For millisecond (ms) precision, encoded values use 8 bytes in this format::

    111PPDDD DDDDDDDD DDDDDDDD DDTTTTTT
    TTTTTTTT TTTSSSSS SSSSSZZZ ZZZZ0000

  Example: *1983-01-15T18:25:12.123+01:00* (millisecond precision) is encoded as
  ``11100011 11011111 10000011 10100100 11001001 10000011 11011100 01000000``
  (bits) or ``e3 df 83 a4 c9 83 dc 40`` (hex bytes).

* For microsecond (µs) precision, encoded values use 9 bytes in this format::

    111PPDDD DDDDDDDD DDDDDDDD DDTTTTTT
    TTTTTTTT TTTSSSSS SSSSSSSS SSSSSSSZ
    ZZZZZZ00

  Example: *1983-01-15T18:25:12.123456+01:00* (microsecond precision) is encoded
  as ``11101011 11011111 10000011 10100100 11001001 10000011 11000100 10000001
  00010000`` (bits) or ``eb df 83 a4 c9 83 c4 81 10`` (hex bytes).

* For nanosecond (ns) precision, encoded values use 10 bytes in this format::

    111PPDDD DDDDDDDD DDDDDDDD DDTTTTTT
    TTTTTTTT TTTSSSSS SSSSSSSS SSSSSSSS
    SSSSSSSS SZZZZZZZ

  Example: *1983-01-15T18:25:12.123456789+01:00* (nanosecond precision) is encoded
  as ``11110011 11011111 10000011 10100100 11001001 10000011 10101101 11100110
  10001010 11000100`` (bits) or ``f3 df 83 a4 c9 83 ad e6 8a c4`` (hex bytes).

* In case the sub-second precision component has no value, encoded values use 7
  bytes in this format::

    111PPDDD DDDDDDDD DDDDDDDD DDTTTTTT
    TTTTTTTT TTTZZZZZ ZZ000000

  Example: *1983-01-15T18:25:12+01:00* (no precision) is encoded as ``11111011
  11011111 10000011 10100100 11001001 10010001 00000000`` (bits) or ``fb df 83 a4
  c9 91 00`` (hex bytes).


Implementations
===============

Python
------

A Python library for *temporenc*, conveniently named *temporenc*, is available
from `PyPI <https://pypi.python.org/pypi/temporenc>`_. The `online documentation
<http://temporenc.readthedocs.org/>`_ is a good place to start.

Rust
----

A (work in progress) implementation for Rust, named *rust-temporenc*,
can be found at the `rust-temporenc project page
<https://bitbucket.org/marshallpierce/rust-temporenc>`_.

Other languages
---------------

Implementations for other languages are most welcome!


Questions and answers
=====================

* Why the name *temporenc*?

  *Temporenc* is a contraction of the words *tempore* (declension of Latin
  *tempus*, meaning *time*) and *enc* (abbreviation for *encoding*). The name
  *temporenc* should only be capitalized when normal spelling rules dictate so,
  e.g. at the start of a sentence.

* What's so novel about *temporenc*?

  Not much. Many ancient civilizations had their methods for representing dates
  and times, and digital schemes for doing the same have been around for
  decades.

  *Temporenc* is just an attempt to cleverly combine what others have been doing
  for a very long time. *Temporenc* uses common bit packing techniques and
  builds upon international standards for representing dates, times, and time
  zones. All *temporenc* is about is combining existing ideas into a
  comprehensive encoding format.

* Why another format when there are already so many of them?

  Indeed, there are many (semi-)standardized formats to represent dates and
  times. Examples include Unix time (elapsed time since an epoch), ISO 8601
  strings (a very extensive ISO standard with many different string formats),
  and SQL ``DATETIME`` strings.

  Each of these formats, including *temporenc*, have their own
  strengths and weaknesses. Some formats allow for missing values
  (e.g. *temporenc*), while others do not (e.g. Unix time). Some can
  represent leap seconds (e.g. ISO 8601, *temporenc*) , while others
  cannot (e.g. Unix time). Some are human readable (e.g. ISO 8601),
  some are not (e.g. *temporenc*, Unix time).

  *Temporenc* provides just a different trade-off that favours encoded space and
  flexibility over human readability and parsing convenience.

* Is *temporenc* just a binary ISO 8601 representation?

  Yes and no. ISO 8601 is a very extensive standard that defines many
  string representations. The *temporenc* *type* ``DTSZ`` is
  conceptually similar to the canonical string format in ISO 8601, but
  it differs in an important way: *temporenc* allows any field to be
  empty, while (some profiles of) ISO 8601 allow only the least
  significant fields to be left empty.

* Why does *temporenc* use so many variable-sized components?

  The *type tags* and packing formats are designed to minimize the
  size of the encoded byte string. For example, by using a 2-bit *type
  tag* for ``DT`` values (date with time), the date (21 bits) and time
  (17 bits) components can be very densely packed into exactly 5 bytes
  (2+21+17=40 bits).

* How does *temporenc* relate to other serialization formats like *MessagePack*,
  *Thrift*, or *Protocol buffers*?

  *Temporenc* only concerns itself with the encoding of date and time
  information into byte strings, not with the serialization of nested data
  structures. This means encoded *temporenc* values can simply be used inside
  larger data structures, which can then be serialized using a generic
  serialization format like *MessagePack* (which supports raw byte strings).
  Upon decoding, the raw byte string is made available again, which a
  *temporenc* decoder can then parse into the original date and time
  information.

* Who came up with this format?

  *Temporenc* was created by `Wouter Bolsterlee <http://wouter.bolsterl.ee/>`_.
  I'm `wbolster <https://github.com/wbolster/>`_ on Github (star my repositories!),
  and `@wbolster <https://twitter.com/wbolster>`_ on Twitter (follow me!).

* How can I contribute to *temporenc*?

  By using it! The *temporenc* specification itself is maintained in the
  `temporenc repository <https://github.com/wbolster/temporenc>`_ on Github. Do
  get in touch if you feel like it!
