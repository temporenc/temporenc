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

  Encoded values of the same type (such as date/time without timezone) can be
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

*Temporenc* uses a conceptual model for date and time values that consists of
four components:

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

*Temporenc* supports any possible combination of these components, including any
combination of sub-components.


Temporenc types
===============

*Temporenc* defines 6 *types*, each of them being a particular combination of
date, time, sub-second time precision, and time zone information:

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

The canonical type ``DTSZ`` (a superset of all the other types) is the most
flexible and can represent any possible combination of components, but also
consumes the most space.

Applications can use a different type to save space, at the cost of reduced
flexibility. The types are chosen in such a way that both sub-second precision
and time zone support are completely optional; by using the correct type the
storage overhead for unused components can be eliminated completely.


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

Times always use 17 bits, divided in three groups (left-to-right):

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

Sub-second time precision is expressed as either milliseconds (ms), microseconds
(µs), or nanoseconds (ns). Each precision requires a different number of bits,
indicated by a 2-bit precision tag at the front of the encoded value.

* **Milliseconds** (12 bits)

  An integer between 0–999 (both inclusive) represented as 10 bits, preceded by
  the precision tag ``00``.

* **Microseconds** (22 bits)

  An integer between 0–999999 (both inclusive) represented as 20 bits, preceded
  by the precision tag ``01``.

* **Nanoseconds** (32 bits)

  An integer between 0–999999999 (both inclusive) represented as 30 bits,
  preceded by the precision tag ``10``.

* **No sub-second precision** (2 bits)

  Only the precision tag ``11``. Note that if no sub-second precision time
  component is required, using a ``temporenc`` type that does not include this
  component at all is more efficient, e.g. by using ``DTZ`` instead of ``DTSZ``.

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

Time zone information always uses 7 bits. The UTC offset of the time zone
(usually written as ±HH:MM) is expressed as the number of 15 minute increments
from UTC, with the constant 64 added to it to ensure the value is a positive
integer in the range 0–126 (both inclusive). The special value 127 (``0x7f``)
means no value is set.

Examples:

========== ================ ============= =============
UTC offset UTC offset       Encoded value Encoded value
           (15m increments) (decimal)     (bits)
========== ================ ============= =============
+00:00     0                64            ``1000000``
+02:00     8                72            ``1001000``
−06:00     −24              40            ``0101000``
========== ================ ============= =============


Packing it all together
-----------------------

Each *temporenc* type has an associated tag, which is a small bit string used
for packing purposes. The tag is always encoded as the left-most bits of the
first byte.

The tags are chosen to minimize the size of the complete value. For example, by
using 2 bits (``00``) for encoding a date and time, the remaining 38 bits (see
below) make the value fit exactly into 5 bytes.

TODO: packing formats are not properly defined yet

TODO: correct total byte string sizes

========= =========== ============ ============ ============ ============ ============ ============ ============
Type      Tag         Byte 1       Byte 2       Byte 3       Byte 4       Byte 5       Byte 6       Byte 7
========= =========== ============ ============ ============ ============ ============ ============ ============
``D``     ``100``     ``100DDDDD`` ``DDDDDDDD`` ``DDDDDDDD``
``T``     ``1110000`` ``1110000T`` ``TTTTTTTT`` ``TTTTTTTT``
``DT``    ``00``      ``00DDDDDD`` ``DDDDDDDD`` ``DDDDDDDT`` ``TTTTTTTT`` ``TTTTTTTT``
``DTZ``   ``101``     ``101DDDDD`` ``DDDDDDDD`` ``DDDDDDDD`` ``TTTTTTTT`` ``TTTTTTTT`` ``TZZZZZZZ``
``DTS``   ``01``      ``01DDDDDD`` ``DDDDDDDD`` ``DDDDDDDT`` ``TTTTTTTT`` ``TTTTTTTT`` sub-seconds
``DTSZ``  ``110``     ``110DDDDD`` ``DDDDDDDD`` ``DDDDDDDD`` ``TTTTTTTT`` ``TTTTTTTT`` ``Txxxxxxx`` sub-seconds
========= =========== ============ ============ ============ ============ ============ ============ ============

..   D     21, tag 3
..   T     17, tag 7
..   DT    38, tag 2
..   DTZ   45, tag 3
..   DTS   38 with S 40/50/60/70  tag 0/6/4/2, tag 2
..   DTSZ  45 with S 47/57/67/77  tag 1/7/5/3, tag 3 (no S is not a common format)

A decoder must inspect the first byte to determine the total size of the
structure and the way it is packed. FIXME not true with sub-second precision.


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

* Who came up with this format?

  *Temporenc* was devised by `Wouter Bolsterlee
  <https://github.com/wbolster/>`_. Do get in touch if you feel like it!
