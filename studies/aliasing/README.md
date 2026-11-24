# SEW aliasing witnesses

This targeted study exercises the numeric-assignment transformation under explicit aliasing conditions. It records generated source, detector output, and paired native observations so that detected outputs with changed behavior can be inspected directly. The case grid is a mechanism diagnostic rather than a prevalence sample.

Data are in `../../results/aliasing/`; retained implementation source and licensing accompany the producer. From the project root, the following command performs fresh watermark generation and native observation:

```sh
python3 artifact/run.py --output /tmp/markvalidity-aliasing-run \
  studies/aliasing/run_study.py -- --out '{output}'
```

Install the parser dependencies in this directory's `requirements.txt` before replaying the upstream implementation. The common supporting check receives the supplied observations without regenerating the benchmark.
