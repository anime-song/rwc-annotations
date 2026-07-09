# RWC MIDI (aligned)

## History

- Basis are the AIST annotations
- 2026/04: Johannes Zeitler and Stefan Balke
    - re-aligned the MIDIs with DTW for RWC 2.0
    - manually controlled all alignments
- 2026/06: (Stefan Balke and Arda Özgün)
    - added `metadata_mapping_vocals.csv`

## Format Specification

- semicolon-separated file
- temporal resolution: 10 ms
- Column 1 (t): time position in seconds
- Column 2 (f0): Fundamental frequency in Hertz (zeros if no melody preset)

## metadata_mapping_vocals.csv

This file specifies which MIDI tracks contain the singing voice (if present in the track).
