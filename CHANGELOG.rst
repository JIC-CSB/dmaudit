CHANGELOG
=========

This project uses `semantic versioning <http://semver.org/>`_.
This change log uses principles from `keep a changelog <http://keepachangelog.com/>`_.

[Unreleased]
------------

Added
^^^^^


Changed
^^^^^^^


Deprecated
^^^^^^^^^^


Removed
^^^^^^^


Fixed
^^^^^


Security
^^^^^^^^

[0.8.0] - 2019-09-21
--------------------

Changed
^^^^^^^

- Added ``-p/--processes`` option to ``dmaudit report`` to parallelise
  building of tree at the top level
- Output of ``dmaudit report -m`` now reports percentage compressed
- Output of ``dmaudit mimetype`` now reports if the mimetype represents a
  compressed file format


[0.7.1] - 2019-09-18
--------------------

Fixed
^^^^^

- Fixed bug where an empty file caused the mimetype evaluation to crash the tool


[0.7.0] - 2019-09-18
--------------------

Changed
^^^^^^^

- Replaced python-magic with puremagic to get rid of dependency on libmagic


[0.6.0] - 2019-09-18
--------------------

Added
^^^^^

- Added ``dmaudit report`` subcommand (previously this was the functionality in
  ``dmaudit`` command)
- Added ``dmaudit mimetype`` subcommand to be able to test what mimetype
  dmaudit thinks a file has


Changed
^^^^^^^

- Command line interface now takes subcommands


[0.5.0] - 2019-09-17
--------------------

Added
^^^^^

- Added ability to install package using ``pip3``
- Added some basic tests


[0.4.0] - 2019-08-23
--------------------

Added
^^^^^

- Version of dmaudit to report

Fixed
^^^^^

- Fix defect when encountering a subdirectory where the user lacks permissions 


[0.3.0] - 2019-07-15
--------------------

Added
^^^^^

- Made output prettier
- Made script more robust in cases of directories being deleted whilst the
  script is running

Fixed
^^^^^

- Fixed issue that audited directory not displayed when path ends with a /


[0.2.0] - 2019-07-01
--------------------

Added
^^^^^

- Added ``--version`` option
- Added command line option to opt into calculating sizes of text and gzipped files



[0.1.2] - 2019-06-21
--------------------

Fixed
^^^^^

- Issue when adding up sizes of text and gzipped files


[0.1.1] - 2019-06-21
--------------------

Fixed
^^^^^

- Issue when sorting by size



[0.1.0] - 2019-06-21
--------------------

Initial release.
