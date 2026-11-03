# Inkwell (synthetic fixture)

A small document-sharing service. Anyone can sign up for free and create a
workspace. Workspace members read and edit that workspace's documents, create
public share links, and request PDF-style exports that are emailed to them.

Run the existing tests with `node test/run.js`. There is no network, database
or email provider here: storage is in memory and email is a recording fake.
