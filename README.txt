Bika UW
=======

This package contains custom code related to UW.

Installation
============

- run python bootstrap.py
- run bin/buildout
- run bin/zeoserver start
- run bin/client1 start
- visit localhost:8080
- add new site
- select bika UW addon.

Changes
=======

These belong here:

- Translated display strings to conform to UW terminology
- Additional fields on some objects, and modified table and object views to
  disply additional fields

These are being PRed against bika.lims/master:

- Expanded Batch workflow with field default acquisition
- optional Single-service selector
- CAS (and other custom identifiers) registry


Issues
======
LIMS-2462: Import.  Field values not propagated, Sampling date incorrect, general feeling of inconsistency.
LIMS-2464: State of open WO won't advance
