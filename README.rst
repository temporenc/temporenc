=========
temporenc
=========

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
serialization format for dates and times
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


*Temporenc*  is a serialization format to represent date and time information as
raw byte strings.

Features
========

*Temporenc* has the following characteristics:

* **Flexible**

  *Temporenc* support any combination of a date, a time, and a timezone. All
  fields are optional. For example, it is possible to encode a year and a day
  without a month.

* **Compact**

  Encoded values have a variable size between 3 and 10 bytes, depending on the
  components being included. For example, an encoded date uses 3 bytes, and an
  encoded time also takes 3 bytes, but an encoded date with time uses only 5
  bytes. At the other extreme, it takes only 10 bytes to encode a date with time
  using nanosecond precision and a time zone.

* **Self-contained**

  Encoded values contain all information needed for decoding. Consuming
  applications do not have to know which format was used for encoding, since
  this can be discovered by looking at the first byte of the value.

* **Sortable**

  Encoded values of the same *type* (such as date/time without timezone) can be
  sorted using normal lexicographical sorting routines on the encoded byte
  strings, with earlier dates sorting first, and with missing values sorting
  last. Among other benefits, this makes *temporenc* values very suited for use
  as (partial) keys in key/value stores.

* **Time zone support**

  Time zone information is encoded using an UTC offset with 15 minute
  granularity, allowing any time zone in use in the world to be represented.

* **Sub-second precision**

  Time information can optionally have sub-second precision using either
  milliseconds, microseconds, or nanoseconds.


Components and types
====================

*Temporenc* uses a conceptual model for date and time values that consists of
four optional *components*:

* **Date** (``D``)

  This component contains year, month, and day information, each part optional.

* **Time** (``T``)

  This component contains hour, minute, and second information, each part
  optional.

* **Sub-second precision** (``S``)

  This component is a refinement to the time component that allows for a more
  precise time representation.

* **Time zone** (``Z``)

  This component specifies the UTC offset.

Based on these components, *temporenc* defines 6 *types*, each of them being a
particular combination of date, time, sub-second time precision, and time zone
information:

========= =================================================== =======
Type      Description                                         Size
                                                              (bytes)
========= =================================================== =======
``D``     Date                                                3
``T``     Time                                                3
``DT``    Date + time                                         5
``DTZ``   Date + time + time zone                             6
``DTS``   Date + time (with sub-second precision)             6–9
``DTSZ``  Date + time (with sub-second precision) + time zone 7–10
========= =================================================== =======

The canonical *type* ``DTSZ`` (a superset of all the other types) is the most
flexible and can represent any possible combination of components, but also
consumes the most space. Since any component (and sub-component) is optional,
any value (dates, times, and so on) can be encoded using the ``DTSZ`` type.

Applications can use a different *type* to save space, at the cost of reduced
flexibility. The types are chosen in such a way that both sub-second precision
and time zone support are completely optional; by using the correct *type* the
storage overhead for unused components can be eliminated completely.


Encoding rules
==============

Encoding is done in two stages:

* In the first stage, each component is encoded separately, resulting in an
  array of bits. The rules for encoding components is the same for all
  *types*.

* The second stage consists of packing the encoded components into the final
  byte string. The exact packing format depends on the *type* used.

For representing numbers as bit strings, *temporenc* always uses unsigned
big-endian notation, e.g. encoding the number 13 into 5 bits results in the bit
string ``01101`` (8 + 4 + 1).


Date component
--------------

The date component (``D``) always uses 21 bits, divided in three groups
(left-to-right):

* **Year** (12 bits)

  An integer between 0–4094 (both inclusive); the special value 4095 (``0xfff``)
  means no value is set.

* **Month** (4 bits)

  An integer between 0–11 (both inclusive); the special value 15 (``0xf``) means
  no value is set. The first month (January) is encoded as 0, February as 1, and
  so on. Note that this is off-by-one compared to human month numbering.

* **Day of month** (5 bits)

  An integer between 0–30 (both inclusive); the special value 31 (``0x1f``)
  means no value is set. The first day of the month is encoded as 0, the next as
  1. Note that this is off-by-one compared to human day numbering.

Examples:

================ ========== ================ ========= =========
Format           Value      Year             Month      Day
================ ========== ================ ========= =========
year, month, day 1983-01-15 ``011110111111`` ``0000``  ``01110``
year, month      1983-01    ``011110111111`` ``0000``  ``11111``
year             1983       ``011110111111`` ``1111``  ``11111``
month, day       01-15      ``111111111111`` ``0000``  ``01110``
================ ========== ================ ========= =========


Time component
--------------

The time component (``T``) always uses 17 bits, divided in three groups
(left-to-right):

* **Hour** (5 bits)

  An integer between 0–23 (both inclusive); the special value 31 (``0x1f``)
  means no value is set.

* **Minute** (6 bits)

  An integer between 0–59 (both inclusive); the special value 63 (``0x3f``)
  means no value is set.

* **Second** (6 bits)

  An integer between 0–60 (both inclusive); the special value 63 (``0x3f``)
  means no value is set. Note that the value 60 is supported because it is
  required to correctly represent leap seconds.

Examples:

==================== ======== ========== ========== ==========
Format               Value    Hour       Minute     Second
==================== ======== ========== ========== ==========
hour, minute, second 18:25:12 ``10010``  ``110100`` ``001100``
hour, minute         18:25    ``10010``  ``110100`` ``111111``
==================== ======== ========== ========== ==========


Sub-second precision time component
-----------------------------------

The sub-second time precision component (``S``) is expressed as either
milliseconds (ms), microseconds (µs), or nanoseconds (ns). Each precision
requires a different number of bits of storage space. This means that unlike the
other components, this component uses a variable number of bits, indicated by a
2-bit precision tag, referred to as ``P``.

* **Milliseconds** (10 bits value, 2 bits tag)

  An integer between 0–999 (both inclusive) represented as 10 bits.
  The precision tag ``P`` is ``00``.

* **Microseconds** (20 bits value, 2 bits tag)

  An integer between 0–999999 (both inclusive) represented as 20 bits.
  The precision tag ``P`` is ``01``.

* **Nanoseconds** (30 bits value, 2 bits tag)

  An integer between 0–999999999 (both inclusive) represented as 30 bits.
  The precision tag ``P`` is ``10``.

* **No sub-second precision** (0 bits value, 2 bits tag)

  The precision tag ``P`` is ``11``, and no additional information is encoded.
  Note that if no sub-second precision time component is required, using a
  *type* that does not include this component at all is more space efficient,
  e.g. by using ``DTZ`` instead of ``DTSZ``.

Examples:

============ ============ ============= ==================================
Precision    Value        Precision tag ms/µs/ns
============ ============ ============= ==================================
milliseconds 123 ms       ``00``        ``0001111011``
microseconds 123456 µs    ``01``        ``00011110001001000000``
nanoseconds  123456789 ns ``10``        ``000111010110111100110100010101``
none         (not set)    ``11``        (nothing)
============ ============ ============= ==================================


Time zone component
-------------------

The time zone component (``Z``) always uses 7 bits. The UTC offset of the time
zone (usually written as ±HH:MM) is expressed as the number of 15 minute
increments from UTC, with the constant 64 added to it to ensure the value is a
positive integer in the range 0–126 (both inclusive). The special value 127
(``0x7f``) means no value is set.

Examples:

========== ================ ============= =============
UTC offset UTC offset       Encoded value Encoded value
           (15m increments) (decimal)     (bits)
========== ================ ============= =============
+00:00     0                64            ``1000000``
+01:00     4                68            ``1000100``
−06:00     −24              40            ``0101000``
========== ================ ============= =============


Packing complete values
-----------------------

The exact packing format depends on the *type*. Each *type* is therefor assigned
a unique *type tag*, which is a short bit string (see below) at the beginning of
the encoded value that is used for identification purposes. The steps for
creating the final output are:

* Start with an empty byte string.
* Concatenate the *type tag*.
* Concatenate the sub-second precision tag ``P`` (if applicable).
* Concatenate all included components (this depends on the *type*).
* Pad the last byte with zeroes to align it to a complete byte (if needed).

The table below shows the how the components are packed for each *type*:

======== =========== ===== ===== ===== ===== ===== ==============
type     type tag    ``P`` ``D`` ``T`` ``S`` ``Z`` padding
======== =========== ===== ===== ===== ===== ===== ==============
``D``    ``100``             ✓
``T``    ``1010000``               ✓
``DT``   ``00``              ✓     ✓
``DTZ``  ``110``             ✓     ✓           ✓
``DTS``  ``01``        ✓     ✓     ✓     ✓         only if needed
``DTSZ`` ``111``       ✓     ✓     ✓     ✓     ✓   only if needed
======== =========== ===== ===== ===== ===== ===== ==============

The advantages of this approach are:

* The total size of encoded values is very small.

* Encoded values of the same *type* can be sorted lexicographically.

* Since both the *type tag* and the precision tag ``P`` (if any) always fit into
  the first byte, a decoder only needs the first byte to determine the total
  size and layout of the complete value, which is useful for decoding streams of
  data without the need for framing.

The various *temporenc types* are encoded like this:

* **Date** (``D``)

  The *type tag* is ``100``. Encoded values use 3 bytes in this format::

      100DDDDD DDDDDDDD DDDDDDDD

* **Time** (``T``)

  The *type tag* is ``1010000``. Encoded values use 3 bytes in this format::

      1010000T TTTTTTTT TTTTTTTT

* **Date + time** (``DT``)

  The *type tag* is ``00``. Encoded values use 5 bytes in this format::

      00DDDDDD DDDDDDDD DDDDDDDT TTTTTTTT
      TTTTTTTT

* **Date + time + time zone** (``DTZ``)

  The *type tag* is ``110``. Encoded values use 6 bytes in this format::

      110DDDDD DDDDDDDD DDDDDDDD TTTTTTTT
      TTTTTTTT TZZZZZZZ

* **Date + time (with sub-second precision)** (``DTS``)

  The *type tag* is ``01``, followed by the precision tag ``P``.
  Values are zero-padded on the right up to the first byte boundary.

  For millisecond (ms) precision, encoded values use 7 bytes in this format::

    01PPDDDD DDDDDDDD DDDDDDDD DTTTTTTT
    TTTTTTTT TTSSSSSS SSSS0000

  For microsecond (µs) precision, encoded values use 8 bytes in this format::

    01PPDDDD DDDDDDDD DDDDDDDD DTTTTTTT
    TTTTTTTT TTSSSSSS SSSSSSSS SSSSSS00

  For nanosecond (ns) precision, encoded values use 9 bytes in this format::

    01PPDDDD DDDDDDDD DDDDDDDD DTTTTTTT
    TTTTTTTT TTSSSSSS SSSSSSSS SSSSSSSS
    SSSSSSSS

  In case the sub-second precision component has no value set, encoded values
  use 6 bytes in this format::

    01PPDDDD DDDDDDDD DDDDDDDD DTTTTTTT
    TTTTTTTT TT000000

* **Date + time (with sub-second precision) + time zone** (``DTSZ``)

  The *type tag* is ``111``, followed by the precision tag ``P``.
  Values are zero-padded on the right up to the first byte boundary.

  For millisecond (ms) precision, encoded values use 8 bytes in this format::

    111PPDDD DDDDDDDD DDDDDDDD DDTTTTTT
    TTTTTTTT TTTSSSSS SSSSSZZZ ZZZZ0000

  For microsecond (µs) precision, encoded values use 9 bytes in this format::

    111PPDDD DDDDDDDD DDDDDDDD DDTTTTTT
    TTTTTTTT TTTSSSSS SSSSSSSS SSSSSSSZ
    ZZZZZZ00

  For nanosecond (ns) precision, encoded values use 10 bytes in this format::

    111PPDDD DDDDDDDD DDDDDDDD DDTTTTTT
    TTTTTTTT TTTSSSSS SSSSSSSS SSSSSSSS
    SSSSSSSS SZZZZZZZ

  In case the sub-second precision component has no value set, encoded values
  use 7 bytes in this format::

    111PPDDD DDDDDDDD DDDDDDDD DDTTTTTT
    TTTTTTTT TTTZZZZZ ZZ000000


Examples
========

The examples below follow this format:

* human-readable value in ISO 8601 format (general form
  ``YYYY-MM-DDTHH:MM:SS.sssssssss±hh:mm``)
* encoded value as a bit string
* encoded value as bytes (hexadecimal notation)

*Type* ``D``:

* 1983-01-15
* ``10001111 01111110 00001110``
* ``8f 7e 0e``

*Type* ``T``:

* 18:25:12
* ``10100001 00101101 00001100``
* ``a1 2d 0c``

*Type* ``DT``:

* 1983-01-15T18:25:12
* ``00011110 11111100 00011101 00101101 00001100``
* ``1e fc 1d 2d 0c``

*Type* ``DTZ``:

* 1983-01-15T18:25:12+01:00
* ``11001111 01111110 00001110 10010110 10000110 01000100``
* ``cf 7e 0e 96 86 44``

*Type* ``DTS``:

* 1983-01-15T18:25:12.123 (milliseconds)
* ``01000111 10111111 00000111 01001011 01000011 00000111 10110000``
* ``47 bf 07 4b 43 07 b0``

* 1983-01-15T18:25:12.123456 (microseconds)
* ``01010111 10111111 00000111 01001011 01000011 00000111 10001001 00000000``
* ``57 bf 07 4b 43 07 89 00``

* 1983-01-15T18:25:12.123456789 (nanoseconds)
* ``01100111 10111111 00000111 01001011 01000011 00000111 01011011 11001101 00010101``
* ``67 bf 07 4b 43 07 5b cd 15``

* 1983-01-15T18:25:12 (sub-second precision not set)
* ``01110111 10111111 00000111 01001011 01000011 00000000``
* ``77 bf 07 4b 43 00``

*Type* ``DTSZ``:

* 1983-01-15T18:25:12.123+01:00 (milliseconds)
* ``11100011 11011111 10000011 10100101 10100001 10000011 11011100 01000000``
* ``e3 df 83 a5 a1 83 dc 40``

* 1983-01-15T18:25:12.123456+01:00 (microseconds)
* ``11101011 11011111 10000011 10100101 10100001 10000011 11000100 10000001 00010000``
* ``eb df 83 a5 a1 83 c4 81 10``

* 1983-01-15T18:25:12.123456789+01:00 (nanoseconds)
* ``11110011 11011111 10000011 10100101 10100001 10000011 10101101 11100110 10001010 11000100``
* ``f3 df 83 a5 a1 83 ad e6 8a c4``

* 1983-01-15T18:25:12+01:00 (sub-second precision not set)
* ``11111011 11011111 10000011 10100101 10100001 10010001 00000000``
* ``fb df 83 a5 a1 91 00``


Questions and answers
=====================

* Why the name *temporenc*?

  *Temporenc* is a contraction of the words *tempore* (declension of Latin
  *tempus*, meaning *time*) and *enc* (abbreviation for *encoding*).

* Why another format when there are already so many of them?

  Indeed, there are many (semi-)standardized formats to represent dates and
  times. Examples include Unix time (elapsed time since an epoch), ISO 8601
  strings (a very extensive ISO standard with many different string formats),
  and SQL ``DATETIME`` strings.

  Each of these formats, including *temporenc*, have their own strengths and
  weaknesses. Some formats allow for missing values (e.g. *temporenc*), while
  others do not (e.g. Unix time). Some can represent leap seconds (e.g.
  ISO 8601) , while others cannot (e.g. Unix time). Some are human readable
  (e.g. ISO 8601), some are not (e.g. *temporenc*).

  *Temporenc* provides just a different trade-off that favours encoded space and
  flexibility over human readability and parsing convenience.

* What's so novel about *temporenc*?

  Not much, to be honest.

  Many ancient civilizations had their methods for representing dates and times,
  and digital schemes for doing the same have been around for decades.

  *temporenc* is just an attempt to cleverly combine what others have been doing
  for a very long time. *temporenc* uses common bit packing techniques and
  builds upon international standards for representing dates, times, and time
  zones. All *temporenc* is about is combining existing ideas into a
  comprehensive encoding format.

* Why does *temporenc* use so many variable-sized components?

  The *type tags* and packing formats are designed to minimize the size of the
  final encoded byte string. For example, by using a 2-bit *type tag* for ``DT``
  values (date with time), the 38 bits required for representing the actual date
  and time fit exactly into 5 bytes.

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

  *Temporenc* was created by `Wouter Bolsterlee
  <https://github.com/wbolster/>`_.

* How can I contribute to *temporenc*?

  *Temporenc* is maintained in the `temporenc repository
  <https://github.com/wbolster/temporenc>`_ on Github. Do get in touch if you
  feel like it!
