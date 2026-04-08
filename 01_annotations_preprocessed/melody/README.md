# RWC Melody Annotations

Currently, there are melody annotations for the RWC-P subcollection.

**Note:** These annotations are limited to the singing voice in these tracks, i.e. if another instrument takes over the
main melody, it will not be reflected in these annotations.

## History

- Basis are the AIST annotations
- 2026/04: (Stefan Balke and Arda Özgün)
    - converted the file format
    - added zeros if no melody present
    - filled zeros before first annotation and last annotation (i.e. the whole audio file has annotations)

## Format Specification

- semicolon-separated file
- temporal resolution: 10 ms
- Column 1 (t): time position in seconds
- Column 2 (f0): Fundamental frequency in Hertz (zeros if no melody preset)
