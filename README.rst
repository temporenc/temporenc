=========
temporenc
=========

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
serialization format for dates and times
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Introduction
============

*Temporenc*  is a serialisation format to represent date and time information as
raw byte strings.

*Temporenc* has the following characteristics:


* **Flexible**

  *Temporenc* support any combination of a date, a time, and a timezone. In
  addition to that all fields are optional. For example, it is possible to
  encode a year and a day without a month.

* **Compact**

  Encoded values have a variable size between 3 and 11 bytes, depending on the
  components being included. For example, an encoded date uses 3 bytes, and an
  encoded time also takes 3 bytes, but an encoded date with time together use
  only 5 bytes. At the other end of the spectrum, an encoded date with time
  using nanosecond precision, and also a time zone attached, takes 11 bytes.

* **Self-contained**

  Encoded values contain all information needed for decoding. Consuming
  applications do not have to know which format was used for encoding.

* **Sortable**

  Encoded values using the same type (e.g. date/time without timezone) can be
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


Conceptual model
================

The conceptual model used by *temporenc* for date and time values consists of
four components:

* **Date** (``D``)

  This component contains year, month, and day information, each part optional.

* **Time** (``T``)

  This component contains hour, minute, and second information, each part
  optional.

* **Sub-second* precision** (``S``)

  This is a refinement to the time component that allows for a more precise time
  representation.

* **Time zone** (``Z``)

  This component specifies the UTC offset.

A *temporenc* value supports all possible combinations of these components
(including any combination of sub-components), with all parts being optional.


Temporenc types
===============

*Temporenc* defines 9 *types*, each of them being a particular combination of
date, time, sub-second time precision, and time zone information:

========= =================================================== ======= =========
Type      Description                                         Size    Tag
                                                              (bytes)
========= =================================================== ======= =========
``D``     Date                                                3       ``00``
``DT``    Date + time                                         5       ``01``
``DTZ``   Date + time + time zone                             6       ``100``
``DTS``   Date + time (with sub-second precision)             7-10    ``101``
``DTSZ``  Date + time (with sub-second precision) + time zone 8-11    ``110``
``T``     Time                                                3       ``11100``
``TZ``    Time + time zone                                    4       ``11101``
``TS``    Time (with sub-second precision)                    5-8     ``11110``
``TSZ``   Time (with sub-second precision) + time zone        6-9     ``11111``
========= =================================================== ======= =========

The most generic type, ``DTSZ``, can hold any possible combination of
components, but also consumes the most space. Other types have less flexibility
but use less space.

Each type has an associated tag (last column in the table above), which is a
small bit string used for packing purposes (explained below).


Encoding rules
==============

As the first step, each component is encoded separately, resulting in an array
of bits. The rules for encoding components do not depend on the *type* of the
final *temporenc* value.

The second step consists of packing the encoded components into the final byte
string. For space efficiency reasons, the exact packing format depends on the
*type*.

For representing numbers as bit strings, *temporenc* always uses unsigned
big-endian notation, e.g. encoding the number 13 into 5 bits results in the bit
string ``01101``.


Date component
--------------

Dates always use 21 bits, divided in three groups (left-to-right):

* **Year** (12 bits)

  An integer between 0-4094 (both inclusive); the value 4095 (``0xfff``) means
  no value is set.

* **Month** (4 bits)

  An integer between 0-11 (both inclusive); the value 15 (``0xf``) means no
  value is set. The first month (January) is encoded as 0, February as 1, and so
  on. Note that this is off-by-one compared to human month numbering.

* **Day of month** (5 bits)

  An integer between 0-31 (both inclusive); the value 31 (``0x1f``) means no
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


Time component
--------------

Times always use 17 bits, divided in three groups (left-to-right):

* **Hour** (5 bits)

  An integer between 0-23 (both inclusive); the value 31 (``0x1f``) means no
  value is set.

* **Minute** (6 bits)

  An integer between 0-59 (both inclusive); the value 63 (``0x3f``) means no
  value is set.

* **Second** (6 bits)

  An integer between 0-60 (both inclusive); the value 63 (``0x3f``) means no
  value is set. Note that the value 60 is supported because it is required to
  correctly represent leap seconds.

Examples:

==================== ======== ========== ========== ==========
Format               Value    Hour       Minute     Second
==================== ======== ========== ========== ==========
hour, minute, second 18:25:12 ``10010``  ``110100`` ``001100``
hour, minute         18:25    ``10010``  ``110100`` ``111111``
==================== ======== ========== ========== ==========


Sub-second precision time component
-----------------------------------

Sub-second time precision is expressed as either milliseconds (ms), microsecond
(µs), or nanoseconds (ns). All numbers are represented as a multiple of 8 bits
(i.e. whole bytes), with specific padding bits on the left that indicate the
precision in use.

* **Milliseconds** (10 bits, padded to 16 bits)

  An integer between 0-999 (both inclusive). The padding is ``000000``.

* **Microseconds** (20 bits, padded to 24 bits)

  An integer between 0-999999 (both inclusive). The padding is ``0100``.

* **Milliseconds** (30 bits, padded to 32 bits)

  An integer between 0-999999999 (both inclusive). The padding is ``10``.

The resulting bytes look like this:

========= ====== ======= ============ ============ ============ ============
Precision Size   Size    Byte 1       Byte 2       Byte 3       Byte 4
          (bits) (bytes)
========= ====== ======= ============ ============ ============ ============
ms        16     2       ``000000xx`` ``xxxxxxxx``
µs        24     3       ``0100xxxx`` ``xxxxxxxx`` ``xxxxxxxx``
ns        32     4       ``10xxxxxx`` ``xxxxxxxx`` ``xxxxxxxx`` ``xxxxxxxx``
none      8      1       ``11111111``
========= ====== ======= ============ ============ ============ ============

In case no value is present, a single ``0xff`` byte is used instead. Note that
in practice it's often a better choice to simply use a *temporenc* type that
does not include a sub-second precision time component.


Time zone component
-------------------

TODO

, expressed as the offset from UTC

Time zones use 7 bits.

The UTC offset (±HH:MM) is expressed as the number of 15m increments from UTC,
with the constant 64 added to it to ensure the value is a positive number.
Examples:

* UTC: ``1000000`` (decimal 64)

* UTC+0200: ``1001000`` (decimal 72); ``72 - 64 = 8`` quarters, i.e. ``2`` hours

* UTC-0600: ``0101000`` (decimal 40); ``40 - 64 = -24`` quarters, i.e. ``-6``
  hours

Packing type tags and parts
===========================

TODO

The tags are chosen to minimize the size of the complete value. For example, by
using 2 bits (``00``) for encoding a date and time, the remaining 38 bits (see
below) make the value fit exactly into 5 bytes.

A decoder must inspect the first byte to determine the total size of the
structure and the way it is packed. FIXME not true with sub-second precision.

The tag is always encoded as the left-most bits of the first byte, the second
column shows what the first byte looks like.

=========  =======  ============  ============  ============  ============  ============  ============  ============
Type tag   Size     Byte 1        Byte 2        Byte 3        Byte 4        Byte 5        Byte 6        Byte 7
           (bytes)
=========  =======  ============  ============  ============  ============  ============  ============  ============
``00``     5        ``00DDDDDD``  ``DDDDDDDD``  ``DDDDDDDT``  ``TTTTTTTT``  ``TTTTTTTT``
``01``     6        ``01DDDDDD``  ``DDDDDDDD``  ``DDDDDDDT``  ``TTTTTTTT``  ``TTTTTTTT``  sub-seconds
``100``    5        ``100xxxxx``  ``xxxxxxxx``  ``xxxxxxxx``  ``xxxxxxxx``  ``xxxxxxxx``  ``xxxxxxxx``  ``xxxxxxxx``
``101``    5        ``101xxxxx``  ``xxxxxxxx``  ``xxxxxxxx``  ``xxxxxxxx``  ``xxxxxxxx``  ``xxxxxxxx``  ``xxxxxxxx``
``110``    5        ``110xxxxx``  ``xxxxxxxx``  ``xxxxxxxx``  ``xxxxxxxx``  ``xxxxxxxx``  ``xxxxxxxx``  ``xxxxxxxx``
``11100``  5        ``11100xxx``  ``xxxxxxxx``  ``xxxxxxxx``  ``xxxxxxxx``  ``xxxxxxxx``  ``xxxxxxxx``  ``xxxxxxxx``
``11101``  5        ``11101xxx``  ``xxxxxxxx``  ``xxxxxxxx``  ``xxxxxxxx``  ``xxxxxxxx``  ``xxxxxxxx``  ``xxxxxxxx``
``11110``  5        ``11110xxx``  ``xxxxxxxx``  ``xxxxxxxx``  ``xxxxxxxx``  ``xxxxxxxx``  ``xxxxxxxx``  ``xxxxxxxx``
``11111``  5        ``11111xxx``  ``xxxxxxxx``  ``xxxxxxxx``  ``xxxxxxxx``  ``xxxxxxxx``  ``xxxxxxxx``  ``xxxxxxxx``
=========  =======  ============  ============  ============  ============  ============  ============  ============


Frequently asked questions
==========================

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

* What's so novel about *temporenc*?

  Not much, to be honest.

  Many ancient civilizations had their methods for representing dates and times,
  and digital schemes for doing the same have been around for decades.

  *temporenc* is just an attempt to cleverly combine what others have been doing
  for a very long time. *temporenc* uses common bit packing techniques and
  builds upon international standards for representing dates, times, and time
  zones. All *temporenc* is about is combining existing ideas into a
  comprehensive encoding format.

* Who came up with this format?

  *Temporenc* was devised by `Wouter Bolsterlee
  <https://github.com/wbolster/>`_. Do get in touch if you feel like it!
