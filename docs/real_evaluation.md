# True-Fit on real bodies and real size charts

This replaces the synthetic evaluation in the V1 paper (2,000 generated shoppers, 8 fictional brands)
with **real body measurements** and **real brand size charts**.

- **Bodies:** ANSUR II, the public anthropometric survey of the US Army (2012): 4,082 men and 1,986 women.
  Download from <https://www.openlab.psu.edu/ansur2/> (`ANSUR_II_MALE_Public.csv`, `ANSUR_II_FEMALE_Public.csv`).
  Columns used: chest circumference (bust for women), waist circumference, buttock circumference (hips),
  biacromial breadth (shoulder), crotch height (inseam) and stature, converted from mm to cm.
- **Catalog:** `backend/data/real_catalog.json`, 1,722 products from 9 Indian brands, scraped on 19–20 Nov 2026:
  bigbanana, Instafab Plus, My Designation, Nobero, Blackberrys, Jaywalking and Bluorng (men's and unisex),
  Janasya and Angrakhaa (women's). Every product uses the brand's own size chart; products with only a generic
  chart, or a physically implausible one, are left out (see `scraper/fitfinder_scraper/catalog.py`).
  Men's bodies are scored against the 1,308 men's and unisex products, women's against the
  473 women's and unisex products.
- **Engine:** the unchanged True-Fit engine (`app/fit/engine.py`), regular fit preference.

Reproduce (about a minute):

```
cd backend
python -m eval.real_fit_eval --ansur-dir /path/to/folder/with/MALE.csv/and/FEMALE.csv
```

Results are written to `backend/eval/results/real_fit_eval.json`.

## A. Catalog coverage by body type

Share of body × product pairs where the best size scores at least 55 (fits), 75 (good fit) and 90 (True Fit),
and where the body is bigger than the largest size on a primary measurement (size run ends).

| Segment | Bodies | Fits | Good fit | True Fit | Size run ends |
| --- | ---: | ---: | ---: | ---: | ---: |
| Men, mainstream (chest < 110, height < 188) | 2,721 | 58.0% | 22.1% | 6.6% | 0.6% |
| Men, very tall (height ≥ 188, chest < 115) | 105 | 61.4% | 29.0% | 10.8% | 1.1% |
| Men, plus-size (chest ≥ 115, height < 185) | 520 | 67.6% | 13.8% | 5.9% | 10.7% |
| Men, big & tall (chest ≥ 115, height ≥ 185) | 103 | 70.3% | 19.2% | 7.4% | 13.7% |
| Men, chest ≥ 123 cm | 130 | 72.3% | 25.7% | 14.4% | 28.9% |
| Women, mainstream (bust < 104, 157–173 cm) | 1,292 | 60.1% | 39.6% | 16.7% | 1.7% |
| Women, petite (bust < 104, ≤ 157 cm) | 330 | 56.1% | 40.2% | 14.2% | 1.3% |
| Women, tall (bust < 104, ≥ 173 cm) | 100 | 62.2% | 35.2% | 15.1% | 2.3% |
| Women, plus-size (bust ≥ 104) | 264 | 60.1% | 30.8% | 9.8% | 12.7% |

**Reading it.** With seven men's brands, from XXS streetwear to bigbanana's 10XL, mainstream men now get a
good fit in 22.1% of pairs (it was 0.2% with bigbanana alone). The size-run
problem is back for big men: most of the new brands stop at 3XL–5XL, so plus-size and big-and-tall men reach
the end of a size run in 10.7% and 13.7% of
pairs, and men with a chest of 123 cm or more in 28.9%, against
0.6% for mainstream men. That is the gap FitFinder is meant to show: a label
filter would list these products, the engine says the run doesn't reach. Plus-size women hit the end of a run in
12.7% of pairs, about seven times the mainstream rate.

## B. Buying your usual label

A shopper finds the size that fits them (score ≥ 75) on one reference chart, then buys that same label for
every other top or dress. Does the label fit (≥ 75)? When it doesn't, can the engine find another size of the
same product that does?

| | Shoppers | Pairs | Label fits | Label not made in that product | Engine finds a fit when the label fails |
| --- | ---: | ---: | ---: | ---: | ---: |
| Men (reference: bigbanana T-shirt) | 203 | 229,593 | 13.6% | 31.2% | 9.5% |
| Women (reference: Janasya kurta) | 1,379 | 474,376 | 12.5% | 38.7% | 24.1% |

Across brands a size label is a poor guide for both men and women: it fits in about one pair in eight, and the
product often isn't made in that label at all. Only shoppers whose reference label fits them are counted,
which for men means bigbanana's 2XL-and-up customers, so the men's row describes big men buying across brands.
A concrete women's case: Janasya cuts M for a 33–35 in waist, Angrakhaa for about 30 in, so a Janasya M is
around two sizes up at Angrakhaa on waist.

Like the paper's baseline, the engine judges both choices, so this shows the value of reading each chart, not
real-world fit. Angrakhaa's dresses often have smocked or elasticated waists that stretch beyond the chart,
which a chart can't capture.

## C. Robustness to measurement error

Gaussian noise of standard deviation σ added to every measurement of 500 random bodies; share of pairs with a
good fit (≥ 75) whose recommended size changes.

| | σ = 1 cm | σ = 2 cm |
| --- | ---: | ---: |
| Men | 13.7% | 26.4% |
| Women | 12.3% | 26.3% |

Most charts step every 2 in (5.1 cm), so a body near a size boundary flips size with small errors: about one
pair in eight at 1 cm and one in four at 2 cm. The app should tell shoppers near a boundary that two sizes are
close, which the "alternatives" field already supports.

## D. Inseam from height

Only Instafab Plus publishes an inseam (9 distinct trouser charts).
Removing the measured inseam and letting the engine estimate it from height keeps the same recommended size in
93.3% of men's pairs on those trousers. Against ANSUR, crotch height averages
0.48 × height; the engine's 0.45 is about 5 cm lower (median -5.5 cm men,
-4.8 cm women). Crotch height is measured to the floor, while a garment's inseam
usually ends a few centimetres higher, so 0.45 may be reasonable for trousers; it is left unchanged.

## Limitations

- **ANSUR II is US Army personnel, not Indian shoppers.** Soldiers skew fit, and very large bodies are rare
  (85 men above a 125 cm chest, 32 women above a 115 cm bust). The largest sizes FitFinder targets are barely
  tested. An Indian anthropometric dataset would be the better source if one can be obtained.
- **Garment charts.** Blackberrys, Jaywalking and Bluorng publish garment measurements; standard ease is
  subtracted to get body sizes. Jaywalking and Bluorng sell oversized streetwear, cut with more ease than
  standard, so their recommended sizes may run one size too large.
- **Charts are per category, not per garment,** and some products are sold in only a few sizes. Fabric stretch
  isn't modelled.
- **Fit is judged by the engine, not by people.** These results describe how the engine behaves on real data.
  Real fit accuracy still needs post-purchase feedback (right / tight / loose / short / long).
- **Prices and stock** were collected on 19–20 Nov 2026 and will drift. The evaluation ignores stock and uses every
  size on the chart.
