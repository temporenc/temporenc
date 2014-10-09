=========
temporenc
=========

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
serialization format for dates and times
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Introduction
============

*Temporenc* is a serialisation format to represent date and time information as
raw byte strings. It has the following characteristics:


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

* Date (``D``)
  
  This component contains year, month, and day information, each part optional.

* Time (``T``)
  
  This component contains hour, minute, and second information, each part
  optional.

* Sub-second precision (``S``)

  This is a refinement to the time component that allows for a more precise time
  representation.

* Time zone (``Z``)

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

For space efficiency reasons, various common combinations of the components
listed above have their own dedicated encoding rules.

The most generic type, ``DTSZ``, can hold any possible combination of
components, but also consumes the most space. Other types have less flexibility
but use less space.

Each type has an associated tag (last column in the table above), which is a
small bit string used for packing purposes (explained below).


Encoding scheme
===============

As the first step, each component is encoded separately. The rules for encoding
parts does not depend on the *type* of the complete structure.

The second step consists of packing these parts into the final byte string. The
exact packing format depends on the *type*.

All numbers are encoded using unsigned big-endian notation.

Date
----

Dates always use 21 bits, divided in three groups (left-to-right):

* Year (12 bits)

  An integer between 0-4094 (both inclusive); the value 4095 means no value is
  set.

* Month (4 bits)

  An integer between 0-11 (both inclusive); the value 15 means no value is set.
  The first month (January) is encoded as 0, February as 1, and so on. Note that
  this is off-by-one compared to normal month numbering.

* Day of month (5 bits)

  An integer between 0-31 (both inclusive); the value 31 means no value is set.
  The first day of the month is encoded as 0, the next as 1. Note that this is
  off-by-one compared to normal day numbering.


Examples:

================  ==========  ================  =========  =========
Format            Value       Year              Month       Day
================  ==========  ================  =========  =========
year, month, day  2014-10-08  ``011111011110``  ``1001``   ``00111``
year, month       2014-10     ``011111011110``  ``1001``   ``11111``
year              2014        ``011111011110``  ``1111``   ``11111``
month, day        10-08       ``111111111111``  ``1001``   ``00111``
================  ==========  ================  =========  =========


Time
----

TODO

Dates always use 17 bits, divided in three groups (left-to-right):

* Hour (5 bits)

  An integer between 0-23 (both inclusive); the value 31 means no value is set.

* Minute: 6 bits (decimal 63 means no value)
* Second: 6 bits (decimal 63 means no value)


Sub-second precision time
-------------------------

TODO

expressed as either milliseconds (ms), microsecond (µs), or nanoseconds (ns)

* Sub-second time precision is encoded using either 10, 20, or 30 bits, depending
  on the precision used:

  * Millisecond: 10 bits
  * Microsecond: 20 bits
  * Nanosecond: 30 bits


Time zone
---------

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
