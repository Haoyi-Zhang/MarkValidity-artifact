# Citation evidence

`verified-sources.json` records the primary or author-source passages actually inspected. `claim-reviews.json` associates each assessed claim with its exact manuscript paragraph and the scope supported by that source.

`audit.json` and `citation-positions.csv` index the current bibliography and manuscript. The local index checks citation keys, source locators, metadata and paragraph bindings. A changed or unassessed paragraph keeps its explicit assessment state until a reviewer checks it.

The companion `../citation-evidence/` directory retains metadata only for references in the current bibliography. The scientific check verifies the local source bindings; it does not automatically renew a source reading or claim assessment.
