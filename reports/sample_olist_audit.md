# Funnel Audit — Olist MQL -> Won funnel
_Generated 2026-10-10 01:02_

## 🟡 Biggest leak: MQL -> Won

7,158 entrants lost between MQL and Won (89.5% of the MQL stage). This is where the funnel bleeds most in absolute terms.

| metric | value |
|---|---|
| from_stage | MQL |
| to_stage | Won |
| lost | 7158 |
| leak_rate | 0.8948 |

## 🟡 Underperformer: origin = display

display converts at 5.1% on 118 MQLs — well below the 10.5% average. Worth investigating before spending more here.

| metric | value |
|---|---|
| dimension | origin |
| value | display |
| mqls | 118 |
| won | 6 |
| conversion_rate | 0.0508 |
| overall_rate | 0.1052 |

## 🟡 Underperformer: origin = email

email converts at 3.0% on 493 MQLs — well below the 10.5% average. Worth investigating before spending more here.

| metric | value |
|---|---|
| dimension | origin |
| value | email |
| mqls | 493 |
| won | 15 |
| conversion_rate | 0.0304 |
| overall_rate | 0.1052 |

## 🟡 Underperformer: origin = other

other converts at 2.7% on 150 MQLs — well below the 10.5% average. Worth investigating before spending more here.

| metric | value |
|---|---|
| dimension | origin |
| value | other |
| mqls | 150 |
| won | 4 |
| conversion_rate | 0.0267 |
| overall_rate | 0.1052 |

## 🟡 Underperformer: origin = social

social converts at 5.6% on 1,350 MQLs — well below the 10.5% average. Worth investigating before spending more here.

| metric | value |
|---|---|
| dimension | origin |
| value | social |
| mqls | 1350 |
| won | 75 |
| conversion_rate | 0.0556 |
| overall_rate | 0.1052 |

## 🟡 Attribution gap

1,159 of 8,000 MQLs (14.5%) have no usable origin — every slice built on this dimension is understated by that much.

| metric | value |
|---|---|
| dimension | origin |
| unknown_count | 1159 |
| unknown_share | 0.1449 |

## 🟢 Overall funnel: MQL -> Won

8,000 MQLs entered, 842 won (10.5% conversion). 7,158 lost (89.5%).

| metric | value |
|---|---|
| mqls | 8000 |
| won | 842 |
| conversion_rate | 0.1052 |
| lost | 7158 |

## 🟢 Outperformer: business_segment = home_decor

home_decor converts at 100.0% on 105 MQLs — well above the 10.5% average. Candidate for more investment.

| metric | value |
|---|---|
| dimension | business_segment |
| value | home_decor |
| mqls | 105 |
| won | 105 |
| conversion_rate | 1.0 |
| overall_rate | 0.1052 |

## 🟢 Outperformer: lead_type = industry

industry converts at 100.0% on 123 MQLs — well above the 10.5% average. Candidate for more investment.

| metric | value |
|---|---|
| dimension | lead_type |
| value | industry |
| mqls | 123 |
| won | 123 |
| conversion_rate | 1.0 |
| overall_rate | 0.1052 |

## 🟢 Outperformer: lead_type = offline

offline converts at 100.0% on 104 MQLs — well above the 10.5% average. Candidate for more investment.

| metric | value |
|---|---|
| dimension | lead_type |
| value | offline |
| mqls | 104 |
| won | 104 |
| conversion_rate | 1.0 |
| overall_rate | 0.1052 |

## 🟢 Outperformer: lead_type = online_big

online_big converts at 100.0% on 126 MQLs — well above the 10.5% average. Candidate for more investment.

| metric | value |
|---|---|
| dimension | lead_type |
| value | online_big |
| mqls | 126 |
| won | 126 |
| conversion_rate | 1.0 |
| overall_rate | 0.1052 |

## 🟢 Outperformer: lead_type = online_medium

online_medium converts at 100.0% on 332 MQLs — well above the 10.5% average. Candidate for more investment.

| metric | value |
|---|---|
| dimension | lead_type |
| value | online_medium |
| mqls | 332 |
| won | 332 |
| conversion_rate | 1.0 |
| overall_rate | 0.1052 |

## 🟢 Outperformer: lead_behaviour_profile = cat

cat converts at 100.0% on 407 MQLs — well above the 10.5% average. Candidate for more investment.

| metric | value |
|---|---|
| dimension | lead_behaviour_profile |
| value | cat |
| mqls | 407 |
| won | 407 |
| conversion_rate | 1.0 |
| overall_rate | 0.1052 |

## 🟢 Outperformer: lead_behaviour_profile = eagle

eagle converts at 100.0% on 123 MQLs — well above the 10.5% average. Candidate for more investment.

| metric | value |
|---|---|
| dimension | lead_behaviour_profile |
| value | eagle |
| mqls | 123 |
| won | 123 |
| conversion_rate | 1.0 |
| overall_rate | 0.1052 |

## 🟢 Best origin at volume: paid_search

Among attributable origin values with 100+ MQLs, paid_search converts best at 12.3% on 1,586 MQLs.

| metric | value |
|---|---|
| origin | paid_search |
| mqls | 1586 |
| conversion_rate | 0.123 |

## 🟢 Time to close

Median MQL -> won is 14 days. Slowest and fastest origins are visible in the evidence — speed differences are a second dimension of channel quality.

| metric | value |
|---|---|
| median_days_to_close | 14.0 |
| median_days_by_origin | {'direct_traffic': 10.0, 'display': 8.0, 'email': 21.0, 'organic_search': 14.0, 'other': 9.0, 'other_publicities': 35.0, 'paid_search': 15.0, 'referral': 18.0, 'social': 30.0, 'unknown': 11.0} |

---
_Every finding above ships with its evidence. Methods: see `--show-work` output._