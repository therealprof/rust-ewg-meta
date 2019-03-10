#!/usr/bin/env python3

# https://github.com/southparkcommons/slacktivate/blob/23d4eb850b28a503a68441bb6dba4006a8595aea/lib/paper.py

import dropbox
import os
import sys

DOC_ID = "5pdv734N8KpxHFMJijuoL"

if len(sys.argv) < 2:
    print("Usage: %s <output.md>" % sys.argv[0])
    sys.exit(1)
filename = sys.argv[1]

TOKEN = os.getenv('DROPBOX_TOKEN')
if TOKEN is None:
    print("DROPBOX_TOKEN env var is not set")
    sys.exit(1)

print("Authenticating...")
dbx = dropbox.Dropbox(TOKEN)

print("Fetching the document...")
doc, res = dbx.paper_docs_download(DOC_ID, dropbox.paper.ExportFormat('markdown'))

print("Document title: '%s', revision %d" % (doc.title, doc.revision))

data = res.text
res.close()

# We have bytes presented as UTF8 string, so decode them first
print("Decoding...")
data = bytes(map(ord, data)).decode()

print("Saving...")
f = open(filename, "wt")
f.write(data)
f.close()
