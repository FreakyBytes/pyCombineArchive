pyCombineArchive
================
*A pure python library to create, modify and read [COMBINE Archives](http://co.mbine.org/documents/archive)*

Project Status
--------------

Currently the development of this project is stalled, due to me not working in this field anymore.
This library was initially developed to implement support for COMBINE Archives in [JWS Online](http://jjj.biochem.sun.ac.za/).
For this purpose it is feature complete, implementing base create, read, update operations for both files within a COMBINE Archive
and their respective meta data encoded in the OMEX format.

If you wish to continue development and maintainance, please contact me.
You may also want to take a look into the [mailing list discussion](https://groups.google.com/forum/#!topic/combine-archive/oRQCoZfUblY),
for alternatives to this library. 

Running Tests
-------------
runs all unit tests and generates a code coverage report.
Please note, that the unit tests of this library are using test CombineArchives from the [SEMS CombineArchive library](https://sems.uni-rostock.de/trac/combinearchive) for Java

```
coverage run --source=. -m unittest discover -s tests/ -p "test_*.py"
coverage report
```

License
-------
This library is licensed under the BSD-3-Clause

	Copyright (c) 2016, Martin Peters
	All rights reserved.

	Redistribution and use in source and binary forms, with or without
	modification, are permitted provided that the following conditions are met:

	* Redistributions of source code must retain the above copyright notice, this
	  list of conditions and the following disclaimer.

	* Redistributions in binary form must reproduce the above copyright notice,
	  this list of conditions and the following disclaimer in the documentation
	  and/or other materials provided with the distribution.

	* Neither the name of [project] nor the names of its
	  contributors may be used to endorse or promote products derived from
	  this software without specific prior written permission.

	THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
	AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
	IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
	DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
	FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
	DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
	SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
	CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
	OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
	OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

This library also includes a modified version of the Python zipfile module and corresponding unittests, which was released under the PSF LICENSE AGREEMENT.
This modul is shipped as ```custom_zip.py``` and ```test_zipfile.py``` as well as ```custom_support.py```

	1. This LICENSE AGREEMENT is between the Python Software Foundation ("PSF"), and
	   the Individual or Organization ("Licensee") accessing and otherwise using Python
	   2.7.11 software in source or binary form and its associated documentation.

	2. Subject to the terms and conditions of this License Agreement, PSF hereby
	   grants Licensee a nonexclusive, royalty-free, world-wide license to reproduce,
	   analyze, test, perform and/or display publicly, prepare derivative works,
	   distribute, and otherwise use Python 2.7.11 alone or in any derivative
	   version, provided, however, that PSF's License Agreement and PSF's notice of
	   copyright, i.e., "Copyright (c) 2001-2016 Python Software Foundation; All Rights
	   Reserved" are retained in Python 2.7.11 alone or in any derivative version
	   prepared by Licensee.

	3. In the event Licensee prepares a derivative work that is based on or
	   incorporates Python 2.7.11 or any part thereof, and wants to make the
	   derivative work available to others as provided herein, then Licensee hereby
	   agrees to include in any such work a brief summary of the changes made to Python
	   2.7.11.

	4. PSF is making Python 2.7.11 available to Licensee on an "AS IS" basis.
	   PSF MAKES NO REPRESENTATIONS OR WARRANTIES, EXPRESS OR IMPLIED.  BY WAY OF
	   EXAMPLE, BUT NOT LIMITATION, PSF MAKES NO AND DISCLAIMS ANY REPRESENTATION OR
	   WARRANTY OF MERCHANTABILITY OR FITNESS FOR ANY PARTICULAR PURPOSE OR THAT THE
	   USE OF PYTHON 2.7.11 WILL NOT INFRINGE ANY THIRD PARTY RIGHTS.

	5. PSF SHALL NOT BE LIABLE TO LICENSEE OR ANY OTHER USERS OF PYTHON 2.7.11
	   FOR ANY INCIDENTAL, SPECIAL, OR CONSEQUENTIAL DAMAGES OR LOSS AS A RESULT OF
	   MODIFYING, DISTRIBUTING, OR OTHERWISE USING PYTHON 2.7.11, OR ANY DERIVATIVE
	   THEREOF, EVEN IF ADVISED OF THE POSSIBILITY THEREOF.

	6. This License Agreement will automatically terminate upon a material breach of
	   its terms and conditions.

	7. Nothing in this License Agreement shall be deemed to create any relationship
	   of agency, partnership, or joint venture between PSF and Licensee.  This License
	   Agreement does not grant permission to use PSF trademarks or trade name in a
	   trademark sense to endorse or promote products or services of Licensee, or any
	   third party.

	8. By copying, installing or otherwise using Python 2.7.11, Licensee agrees
	   to be bound by the terms and conditions of this License Agreement.
