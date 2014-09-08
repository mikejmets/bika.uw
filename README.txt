Bika UW
=======

This package contains custom code related to UW.

Installation
============

1. Install Plone

    The Unified Installer is the recommended method.

2. Edit buildout.cfg

    Add 'bika.uw' to the eggs and develop sections.

3. Download sources

    cd Plone/zeocluster/src
    git clone git@d1.bikalabs.com:bika/bika.uw

4. Run buildout again

    bin/builodut

5. Activate the bika.uw addon.

    When creating a new site, only "Bika LIMS UW" need be selected.  It
    will install all packages on which it depends.

    If adding bika.uw to an existing site, visit Site Setup -> Addons,
    find the Bika LIMS UW addon in the list, and activate it.

Changes
=======

1. 'Translated' display strings to conform to UW terminology

2. Expanded Batch workflow

3. Additional Batch fields

