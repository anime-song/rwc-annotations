# Changelog

## v2.0.1

- Add melody annotations
- Add manual music start/end annotations
- Add metadata for vocal-MIDI mapping (#260)

## v2.0.0

- Initial version
- Initial conversion from mixed formats to documented CSVs in `01_annotations_preprocessed` for the beat annotations
- Merged the updated annotations from https://github.com/CPJKU/beat_this_annotations/tree/main/rwc/annotations/beats
    - Original AIST annotations were parsed and saved in the "beat_this" annotations format to make both comparable
    - Both versions were sonified and quality checked
    - If differences arose, we created a new pull request per track
    - Per track, we either decided completely for the new or original annotation, merged both, and/or corrected the results

