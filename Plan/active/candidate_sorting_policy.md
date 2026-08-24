# Step 8 Candidate Sorting Policy

This policy makes library selection auditable across PE-Claw 1.0 and 2.0.

1. Registry inputs are treated as data snapshots. Candidate identity is the stable part number or magnetic candidate ID.
2. Semiconductor schemes are compared by explicit scheme ID, parallel count, role, ranking score, loss, junction temperature, and part number.
3. Capacitor entries are compared by the selector score, total loss, volume, parallel count, and part number. The final part-number tie-break is mandatory.
4. Magnetic candidates are compared by the engine's explicit score/Pareto representative policy; chosen candidate IDs and their ordered checksum are retained.
5. No acceptance decision may depend on filesystem enumeration or the incidental order returned by a vendor builder.
6. A different selected part is a library or ranking difference until the candidate-list checksum and field-level evidence explain it.

The runtime golden snapshot records selected identities, parallel counts, representative candidate lists, and checksums for every registered topology.
