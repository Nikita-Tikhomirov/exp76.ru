# Expanded architecture SERP batch

This batch validates the replacement S1-S8 architecture before any page is
staged or published.

- `serp-queue.csv` contains one current Yandex representative query for every
  proposed destination: 44 commercial child services and 48 articles.
- Commercial children are constrained to 5-6 per hub. Articles are a separate
  5-7 page layer and never satisfy the commercial-page minimum.
- Results are collected through the guarded deferred Yandex Search API client.
- A candidate is not production-ready merely because it appears in the queue.
  SERP format, sibling/hub overlap, business-offer evidence and content proof
  must all be reviewed first.
- Protected category owners 87-92 are outside this batch and remain unchanged.

The first batch contains 92 requests. At the configured deferred rate its
maximum estimated cost is 2.8060 RUB.
