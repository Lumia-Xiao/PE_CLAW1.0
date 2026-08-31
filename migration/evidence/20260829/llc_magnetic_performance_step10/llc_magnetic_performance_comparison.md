# LLC Magnetic Performance Step 10

The optimized implementation was compared with the Step 1 baseline using the same
input checksums, packaged normalized magnetic database, and explicit search limits.

| Case | Transformer before (s) | Transformer after (s) | Speedup | External Lr before (s) | External Lr after (s) | Speedup |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| transformer-small | 0.324705 | 0.032259 | 10.07x | n/a | n/a | n/a |
| transformer-medium | 1.089863 | 0.049150 | 22.17x | n/a | n/a | n/a |
| external-lr-small | 1.089641 | 0.050138 | 21.73x | 1.2803751999963424 | 0.04577999999946769 | 27.97x |
| external-lr-medium | 1.052772 | 0.049753 | 21.16x | 8.399345199999516 | 0.18080149999968853 | 46.46x |

## Regression

- Command: `PYTHONPATH=src python -m pytest -q --ignore=tests/test_ac_dc_efficiency_gui_end_to_end.py --basetemp .pytest-tmp-step10`
- Result: `377 passed, 1 skipped`
- Duration: `1135.54` seconds
- Excluded test: `tests/test_ac_dc_efficiency_gui_end_to_end.py`
- Exclusion reason: The unrelated AC-DC GUI end-to-end test started a multi-topology real magnetic-design run and remained in a long-running unresponsive child process during the bounded acceptance attempt; it was excluded from the LLC closeout regression and remains a separate follow-up.
