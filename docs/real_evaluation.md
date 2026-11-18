# True-Fit on real bodies and real size charts

This replaces the synthetic evaluation in the V1 paper (2,000 generated shoppers, 8 fictional brands)
with **real body measurements** and **real brand size charts**.

- **Bodies:** ANSUR II, the public anthropometric survey of the US Army (2012): 4,082 men and 1,986 women.
  Download from <https://www.openlab.psu.edu/ansur2/> (`ANSUR_II_MALE_Public.csv`, `ANSUR_II_FEMALE_Public.csv`).
  Columns used: chest circumference (bust for women), waist circumference, buttock circumference (hips),
  biacromial breadth (shoulder), crotch height (inseam) and stature, converted from mm to cm.
- **Catalog:** `backend/data/real_catalog.json`, 653 products scraped on 19 Nov 2026 from bigbanana
  (men, 250), Janasya (women, 213) and Angrakhaa (women, 190). 98% use the brand's own size chart.
  Men are scored against bigbanana, women against Janasya and Angrakhaa.
- **Engine:** the unchanged True-Fit engine (`app/fit/engine.py`), regular fit preference.

Reproduce (about 30 seconds):

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
| Men, mainstream (chest < 110, height < 188) | 2,721 | 1.7% | 0.2% | 0.0% | 0.0% |
| Men, very tall (height ≥ 188, chest < 115) | 105 | 4.0% | 1.1% | 0.4% | 0.0% |
| Men, plus-size (chest ≥ 115, height < 185) | 520 | 40.3% | 22.1% | 13.8% | 0.0% |
| Men, big & tall (chest ≥ 115, height ≥ 185) | 103 | 56.0% | 36.6% | 23.7% | 0.0% |
| Men, chest ≥ 123 cm (bigbanana's 2XL and up) | 130 | 98.1% | 88.6% | 69.2% | 0.0% |
| Women, mainstream (bust < 104, 157–173 cm) | 1,292 | 63.2% | 45.8% | 19.4% | 2.2% |
| Women, petite (bust < 104, ≤ 157 cm) | 330 | 60.2% | 46.9% | 16.7% | 1.7% |
| Women, tall (bust < 104, ≥ 173 cm) | 100 | 63.4% | 39.7% | 17.3% | 2.7% |
| Women, plus-size (bust ≥ 104) | 264 | 56.1% | 36.6% | 11.5% | 13.5% |

**Reading it.** bigbanana is a plus-size specialist whose smallest size (2XL) starts at a 123 cm chest, so it
fits almost no mainstream men, and that is correct, not a failure. For men inside its range it gives a good
fit in 88.6% of pairs. No ANSUR man is larger than bigbanana's largest size (its run reaches a 170–182 cm chest,
ANSUR's largest man is 147 cm), so the "size run ends" problem the synthetic study showed for big men
does not appear here. For women, plus-size shoppers reach the end of a size run in 13.5% of pairs,
six times the mainstream rate, because many products are sold only up to 2XL or 3XL.

## B. Buying your usual label

A shopper finds the size that fits them (score ≥ 75) on one reference chart, then buys that same label for
every other top or dress. Does the label fit (≥ 75)? When it doesn't, can the engine find another size of the
same product that does?

| | Shoppers | Pairs | Label fits | Label not made in that product | Engine finds a fit when the label fails |
| --- | ---: | ---: | ---: | ---: | ---: |
| Men (reference: bigbanana T-shirt) | 203 | 40,397 | 75.0% | 0.0% | 0.0% |
| Women (reference: Janasya kurta) | 1,379 | 380,604 | 14.9% | 44.0% | 32.0% |

Within one brand (men, all bigbanana) the label fits three times in four; the quarter that fails does not fit
in any size either, so reading the chart doesn't help. Across brands (women) the label is a poor guide: it fits
in 14.9% of pairs, the product isn't made in that label in 44%, and in 32% of the failures another size of the
same product fits. A concrete case: Janasya cuts M for a 33–35 in waist, Angrakhaa for about 30 in, so a Janasya
M is around two sizes up at Angrakhaa on waist.

Like the paper's baseline, the engine judges both choices, so this shows the value of reading each chart, not
real-world fit. Angrakhaa's dresses often have smocked or elasticated waists that stretch beyond the chart,
which a chart can't capture.

## C. Robustness to measurement error

Gaussian noise of standard deviation σ added to every measurement of 500 random bodies; share of pairs with a
good fit (≥ 75) whose recommended size changes.

| | σ = 1 cm | σ = 2 cm |
| --- | ---: | ---: |
| Men (bigbanana) | 4.0% | 3.7% |
| Women (Janasya, Angrakhaa) | 12.1% | 26.0% |

Women's charts step every 2 in (5.1 cm) and are checked on bust, waist and hips together, so a body near a
size boundary on any one of them flips size with small errors. The app should tell women near a boundary that
two sizes are close, which the "alternatives" field already supports.

## D. Inseam from height

None of the real bottoms publish an inseam, so the inseam estimate never affects a recommendation in this
catalog. Against ANSUR, crotch height averages 0.48 × height (0.48 for women too); the engine's 0.45 is about
5 cm lower (median −5.5 cm men, −4.8 cm women). Crotch height is measured to the floor, while a garment's inseam
usually ends a few centimetres higher, so 0.45 may be reasonable for trousers. This needs garment inseam data
to settle and is left unchanged.

## Limitations

- **ANSUR II is US Army personnel, not Indian shoppers.** Soldiers skew fit, and very large bodies are rare
  (85 men above a 125 cm chest, 32 women above a 115 cm bust). The largest sizes FitFinder targets are barely
  tested. An Indian anthropometric dataset would be the better source if one can be obtained.
- **Charts are per category, not per garment,** and some products are sold in only a few sizes. Fabric stretch
  isn't modelled.
- **Fit is judged by the engine, not by people.** These results describe how the engine behaves on real data.
  Real fit accuracy still needs post-purchase feedback (right / tight / loose / short / long).
- **Prices and stock** were collected on 19 Nov 2026 and will drift. The evaluation ignores stock and uses every
  size on the chart.
