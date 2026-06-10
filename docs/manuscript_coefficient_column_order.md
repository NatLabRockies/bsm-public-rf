# Coefficient Matrix Column Order

Canonical column order for the 132-feature reduced-form coefficient matrix (`artifacts/final_model/coefficient_matrix_raw_scale.csv` and `coefficient_matrix_standardized.csv`). Each row pairs the column position with its feature name, transformation, base input(s), units, sample range, and the feature's contribution metrics.

**Total columns:** 132. **Source of truth for column order:** `artifacts/final_model/final_support_features.csv` (field `final_support_position`).

| Idx | Feature name | Transform | Base input 1 | Unit | Min | Max | Pathway | n_out≠0 | Δ nRMSE if removed |
| --- | ------------ | --------- | ------------ | ---- | --- | --- | ------- | ------- | ------------------ |
| 0 | `OHC.PY sensi multiplier[HEFA]` | identity | `OHC.PY sensi multiplier[HEFA]` | unitless | 0.75 | 1.25 | Oilcrop HEFA | 3802 | 0.6144 |
| 1 | `WW.PY sensi multiplier[SludgeToHTL]` | identity | `WW.PY sensi multiplier[SludgeToHTL]` | unitless | 0.75 | 1.25 | Sewage Sludge HTL | 2815 | 0.3025 |
| 2 | `inverse_OHC.PY sensi multiplier[HEFA]` | inverse | `OHC.PY sensi multiplier[HEFA]` | unitless | 0.75 | 1.25 | Oilcrop HEFA | 4203 | 0.2511 |
| 3 | `WW.PY sensi multiplier[SludgeToHTL]:WW.progress ratios commercial[SludgeToHTL]` | interaction | `WW.PY sensi multiplier[SludgeToHTL]` | unitless | 0.75 | 1.25 | Sewage Sludge HTL | 2582 | 0.1976 |
| 4 | `sqrt_AHC.PY sensi multiplier[HEFA]` | sqrt | `AHC.PY sensi multiplier[HEFA]` | unitless | 0.75 | 1.25 | Algal HEFA | 498 | 0.4364 |
| 5 | `WW.Mature Industry Rate of Return as PCT[SludgeToHTL]:WW.progress ratios commercial[SludgeToHTL]` | interaction | `WW.Mature Industry Rate of Return as PCT[SludgeToHTL]` | %/yr | 5.0 | 15.0 | Sewage Sludge HTL | 3070 | 0.0890 |
| 6 | `WW.Mature Industry Rate of Return as PCT[SludgeToHTL]` | identity | `WW.Mature Industry Rate of Return as PCT[SludgeToHTL]` | %/yr | 5.0 | 15.0 | Sewage Sludge HTL | 4352 | 0.1078 |
| 7 | `sqrt_AHC.PY sensi multiplier[HTL]` | sqrt | `AHC.PY sensi multiplier[HTL]` | unitless | 0.75 | 1.25 | Algal HTL | 750 | 0.3399 |
| 8 | `OHC.PY sensi multiplier[HEFABrownfield]:OHC.PY sensi multiplier[HEFA]` | interaction | `OHC.PY sensi multiplier[HEFABrownfield]` | unitless | 0.75 | 1.25 | Oilcrop HEFA (Brownfield) | 4205 | 0.1672 |
| 9 | `WW.PY sensi multiplier[ManureToHTL]` | identity | `WW.PY sensi multiplier[ManureToHTL]` | unitless | 0.75 | 1.25 | Manure HTL | 1328 | 0.0630 |
| 10 | `CHC.PY sensi multiplier[Thermochem]:CHC.Mature Industry Rate of Return as PCT[Thermochem]` | interaction | `CHC.PY sensi multiplier[Thermochem]` | unitless | 0.75 | 1.25 | Cellulosic Thermochem | 5938 | 0.0854 |
| 11 | `AHC.PY sensi multiplier[HEFA]` | identity | `AHC.PY sensi multiplier[HEFA]` | unitless | 0.75 | 1.25 | Algal HEFA | 494 | 0.1661 |
| 12 | `AHC.PY sensi multiplier[HTL]` | identity | `AHC.PY sensi multiplier[HTL]` | unitless | 0.75 | 1.25 | Algal HTL | 757 | 0.1309 |
| 13 | `CHC.PY sensi multiplier[Thermochem]:CHC.initial indices of Commercial Maturity[Thermochem]` | interaction | `CHC.PY sensi multiplier[Thermochem]` | unitless | 0.75 | 1.25 | Cellulosic Thermochem | 5162 | 0.0330 |
| 14 | `CHC.Mature Industry Rate of Return as PCT[Brownfield]` | identity | `CHC.Mature Industry Rate of Return as PCT[Brownfield]` | %/yr | 5.0 | 15.0 | Cellulosic Thermochem (Brownfield) | 2881 | 0.0735 |
| 15 | `CHC.initial indices of Commercial Maturity[Brownfield]:CHC.PY sensi multiplier[Brownfield]` | interaction | `CHC.initial indices of Commercial Maturity[Brownfield]` | unitless | 0.0 | 0.7 | Cellulosic Thermochem (Brownfield) | 4575 | 0.0370 |
| 16 | `CHC.Mature Industry Rate of Return as PCT[Thermochem]` | identity | `CHC.Mature Industry Rate of Return as PCT[Thermochem]` | %/yr | 5.0 | 15.0 | Cellulosic Thermochem | 4850 | 0.0521 |
| 17 | `OHC.PY sensi multiplier[HEFABrownfield]` | identity | `OHC.PY sensi multiplier[HEFABrownfield]` | unitless | 0.75 | 1.25 | Oilcrop HEFA (Brownfield) | 2940 | 0.6406 |
| 18 | `WW.PY sensi multiplier[ManureToHTL]:WW.Mature Industry Rate of Return as PCT[ManureToHTL]` | interaction | `WW.PY sensi multiplier[ManureToHTL]` | unitless | 0.75 | 1.25 | Manure HTL | 2832 | 0.0167 |
| 19 | `CHC.PY sensi multiplier[Thermochem]:CHC.FCI  sensi multiplier[Thermochem]` | interaction | `CHC.PY sensi multiplier[Thermochem]` | unitless | 0.75 | 1.25 | Cellulosic Thermochem | 5052 | 0.0926 |
| 20 | `CHC.PY sensi multiplier[Thermochem]` | identity | `CHC.PY sensi multiplier[Thermochem]` | unitless | 0.75 | 1.25 | Cellulosic Thermochem | 6283 | 0.2271 |
| 21 | `CHC.initial indices of Commercial Maturity[Brownfield]:CHC.Mature Industry Rate of Return as PCT[Brownfield]` | interaction | `CHC.initial indices of Commercial Maturity[Brownfield]` | unitless | 0.0 | 0.7 | Cellulosic Thermochem (Brownfield) | 5348 | 0.0245 |
| 22 | `OHC.PY sensi multiplier[HEFA]:OHC.progress ratios commercial[HEFA]` | interaction | `OHC.PY sensi multiplier[HEFA]` | unitless | 0.75 | 1.25 | Oilcrop HEFA | 2525 | 0.1302 |
| 23 | `WW.progress ratios commercial[SludgeToHTL]:WW.FCI  sensi multiplier[SludgeToHTL]` | interaction | `WW.progress ratios commercial[SludgeToHTL]` | 1/doubling | 0.65 | 0.85 | Sewage Sludge HTL | 2427 | 0.0610 |
| 24 | `CHC.Mature Industry Rate of Return as PCT[Thermochem]:CHC.FCI  sensi multiplier[Thermochem]` | interaction | `CHC.Mature Industry Rate of Return as PCT[Thermochem]` | %/yr | 5.0 | 15.0 | Cellulosic Thermochem | 4259 | 0.0282 |
| 25 | `CHC.FCI  sensi multiplier[Thermochem]` | identity | `CHC.FCI  sensi multiplier[Thermochem]` | unitless | 0.75 | 1.25 | Cellulosic Thermochem | 4131 | 0.0895 |
| 26 | `inverse_WW.PY sensi multiplier[ManureToHTL]` | inverse | `WW.PY sensi multiplier[ManureToHTL]` | unitless | 0.75 | 1.25 | Manure HTL | 1209 | 0.0312 |
| 27 | `CHC.Mature Industry Rate of Return as PCT[Thermochem]:CHC.initial indices of Commercial Maturity[Thermochem]` | interaction | `CHC.Mature Industry Rate of Return as PCT[Thermochem]` | %/yr | 5.0 | 15.0 | Cellulosic Thermochem | 5523 | 0.0143 |
| 28 | `CHC.initial indices of Commercial Maturity[Brownfield]:CHC.FCI  sensi multiplier[Brownfield]` | interaction | `CHC.initial indices of Commercial Maturity[Brownfield]` | unitless | 0.0 | 0.7 | Cellulosic Thermochem (Brownfield) | 3642 | 0.0169 |
| 29 | `inverse_WW.PY sensi multiplier[SludgeToHTL]` | inverse | `WW.PY sensi multiplier[SludgeToHTL]` | unitless | 0.75 | 1.25 | Sewage Sludge HTL | 3311 | 0.0591 |
| 30 | `CHC.initial indices of Commercial Maturity[Thermochem]:CHC.FCI  sensi multiplier[Thermochem]` | interaction | `CHC.initial indices of Commercial Maturity[Thermochem]` | unitless | 0.1 | 0.7 | Cellulosic Thermochem | 3645 | 0.0114 |
| 31 | `CHC.Mature Industry Rate of Return as PCT[Brownfield]:CHC.PY sensi multiplier[Brownfield]` | interaction | `CHC.Mature Industry Rate of Return as PCT[Brownfield]` | %/yr | 5.0 | 15.0 | Cellulosic Thermochem (Brownfield) | 3380 | 0.0317 |
| 32 | `WW.FCI  sensi multiplier[SludgeToHTL]` | identity | `WW.FCI  sensi multiplier[SludgeToHTL]` | unitless | 0.75 | 1.25 | Sewage Sludge HTL | 2383 | 0.0613 |
| 33 | `WW.PY sensi multiplier[ManureToHTL]:WW.ORNOOC sensi multiplier[ManureToHTL]` | interaction | `WW.PY sensi multiplier[ManureToHTL]` | unitless | 0.75 | 1.25 | Manure HTL | 937 | 0.0125 |
| 34 | `OHC.PY sensi multiplier[HEFA]:OHC.Mature Industry Rate of Return as PCT[HEFA]` | interaction | `OHC.PY sensi multiplier[HEFA]` | unitless | 0.75 | 1.25 | Oilcrop HEFA | 2564 | 0.0273 |
| 35 | `OHC.Retirement Frac[TransEster]:OHC.PY sensi multiplier[HEFA]` | interaction | `OHC.Retirement Frac[TransEster]` | unitless | 0.0 | 0.15 | Oilcrop Transesterification | 2128 | 0.0137 |
| 36 | `inverse_WW.progress ratios commercial[SludgeToHTL]` | inverse | `WW.progress ratios commercial[SludgeToHTL]` | 1/doubling | 0.65 | 0.85 | Sewage Sludge HTL | 3628 | 0.3528 |
| 37 | `OHC.Mature Industry Rate of Return as PCT[HEFA]` | identity | `OHC.Mature Industry Rate of Return as PCT[HEFA]` | %/yr | 5.0 | 15.0 | Oilcrop HEFA | 2121 | 0.0281 |
| 38 | `WW.PY sensi multiplier[SludgeToHTL]:WW.ORNOOC sensi multiplier[SludgeToHTL]` | interaction | `WW.PY sensi multiplier[SludgeToHTL]` | unitless | 0.75 | 1.25 | Sewage Sludge HTL | 3360 | 0.0341 |
| 39 | `sqrt_OHC.PY sensi multiplier[HEFABrownfield]` | sqrt | `OHC.PY sensi multiplier[HEFABrownfield]` | unitless | 0.75 | 1.25 | Oilcrop HEFA (Brownfield) | 2962 | 1.2044 |
| 40 | `WW.progress ratios commercial[SludgeToHTL]` | identity | `WW.progress ratios commercial[SludgeToHTL]` | 1/doubling | 0.65 | 0.85 | Sewage Sludge HTL | 3026 | 0.3980 |
| 41 | `WW.ORNOOC sensi multiplier[SludgeToHTL]` | identity | `WW.ORNOOC sensi multiplier[SludgeToHTL]` | unitless | 0.75 | 1.25 | Sewage Sludge HTL | 3272 | 0.0570 |
| 42 | `CHC.Mature Industry Rate of Return as PCT[Biochem]:CHC.FCI  sensi multiplier[Biochem]` | interaction | `CHC.Mature Industry Rate of Return as PCT[Biochem]` | %/yr | 5.0 | 15.0 | Cellulosic Biochem | 870 | 0.0142 |
| 43 | `WW.PY sensi multiplier[ManureToHTL]:WW.initial indices of Commercial Maturity[ManureToHTL]` | interaction | `WW.PY sensi multiplier[ManureToHTL]` | unitless | 0.75 | 1.25 | Manure HTL | 1026 | 0.0032 |
| 44 | `CHC.Mature Industry Rate of Return as PCT[Biochem]:CHC.PY sensi multiplier[Biochem]` | interaction | `CHC.Mature Industry Rate of Return as PCT[Biochem]` | %/yr | 5.0 | 15.0 | Cellulosic Biochem | 442 | 0.0143 |
| 45 | `CHC.Mature Industry Rate of Return as PCT[Biochem]` | identity | `CHC.Mature Industry Rate of Return as PCT[Biochem]` | %/yr | 5.0 | 15.0 | Cellulosic Biochem | 733 | 0.0162 |
| 46 | `OHC.PY sensi multiplier[HEFA]:OHC.FCI  sensi multiplier[HEFA]` | interaction | `OHC.PY sensi multiplier[HEFA]` | unitless | 0.75 | 1.25 | Oilcrop HEFA | 2775 | 0.0376 |
| 47 | `OHC.Retirement Frac[TransEster]:OHC.PY sensi multiplier[HEFABrownfield]` | interaction | `OHC.Retirement Frac[TransEster]` | unitless | 0.0 | 0.15 | Oilcrop Transesterification | 2135 | 0.0203 |
| 48 | `OHC.progress ratios commercial[HEFA]` | identity | `OHC.progress ratios commercial[HEFA]` | 1/doubling | 0.65 | 0.85 | Oilcrop HEFA | 2326 | 0.2106 |
| 49 | `WW.Mature Industry Rate of Return as PCT[ManureToHTL]:WW.ORNOOC sensi multiplier[ManureToHTL]` | interaction | `WW.Mature Industry Rate of Return as PCT[ManureToHTL]` | %/yr | 5.0 | 15.0 | Manure HTL | 1378 | 0.0047 |
| 50 | `WW.PY sensi multiplier[ManureToHTL]:WW.FCI  sensi multiplier[ManureToHTL]` | interaction | `WW.PY sensi multiplier[ManureToHTL]` | unitless | 0.75 | 1.25 | Manure HTL | 1099 | 0.0124 |
| 51 | `WW.Mature Industry Rate of Return as PCT[ManureToHTL]_squared` | quadratic | `WW.Mature Industry Rate of Return as PCT[ManureToHTL]` | %/yr | 5.0 | 15.0 | Manure HTL | 971 | 0.0036 |
| 52 | `WW.Mature Industry Rate of Return as PCT[ManureToHTL]:WW.FCI  sensi multiplier[ManureToHTL]` | interaction | `WW.Mature Industry Rate of Return as PCT[ManureToHTL]` | %/yr | 5.0 | 15.0 | Manure HTL | 933 | 0.0111 |
| 53 | `OHC.Retirement Frac[TransEster]` | identity | `OHC.Retirement Frac[TransEster]` | unitless | 0.0 | 0.15 | Oilcrop Transesterification | 2075 | 0.0310 |
| 54 | `CHC.initial indices of Commercial Maturity[Thermochem]_squared` | quadratic | `CHC.initial indices of Commercial Maturity[Thermochem]` | unitless | 0.1 | 0.7 | Cellulosic Thermochem | 3740 | 0.0036 |
| 55 | `CHC.Mature Industry Rate of Return as PCT[Biochem]:CHC.initial indices of Commercial Maturity[Biochem]` | interaction | `CHC.Mature Industry Rate of Return as PCT[Biochem]` | %/yr | 5.0 | 15.0 | Cellulosic Biochem | 483 | 0.0050 |
| 56 | `CHC.PY sensi multiplier[Thermochem]:WW.Mature Industry Rate of Return as PCT[SludgeToHTL]` | interaction | `CHC.PY sensi multiplier[Thermochem]` | unitless | 0.75 | 1.25 | Cellulosic Thermochem | 4846 | 0.0162 |
| 57 | `CHC.initial indices of Commercial Maturity[Thermochem]` | identity | `CHC.initial indices of Commercial Maturity[Thermochem]` | unitless | 0.1 | 0.7 | Cellulosic Thermochem | 3081 | 0.0097 |
| 58 | `CHC.initial indices of Commercial Maturity[Brownfield]` | identity | `CHC.initial indices of Commercial Maturity[Brownfield]` | unitless | 0.0 | 0.7 | Cellulosic Thermochem (Brownfield) | 2748 | 0.0106 |
| 59 | `inverse_WW.Mature Industry Rate of Return as PCT[SludgeToHTL]` | inverse | `WW.Mature Industry Rate of Return as PCT[SludgeToHTL]` | %/yr | 5.0 | 15.0 | Sewage Sludge HTL | 3166 | 0.0075 |
| 60 | `OHC.FCI  sensi multiplier[HEFA]` | identity | `OHC.FCI  sensi multiplier[HEFA]` | unitless | 0.75 | 1.25 | Oilcrop HEFA | 2738 | 0.0353 |
| 61 | `inverse_SE.Max Jet Investment Hit Rate` | inverse | `SE.Max Jet Investment Hit Rate` | 1/year | 0.05 | 0.3 | Starch Ethanol-to-Jet | 4083 | 0.0060 |
| 62 | `SE.Max Jet Investment Hit Rate` | identity | `SE.Max Jet Investment Hit Rate` | 1/year | 0.05 | 0.3 | Starch Ethanol-to-Jet | 3768 | 0.0243 |
| 63 | `WW.PY sensi multiplier[SludgeToHTL]:AHC.initial indices of Commercial Maturity[HTL]` | interaction | `WW.PY sensi multiplier[SludgeToHTL]` | unitless | 0.75 | 1.25 | Sewage Sludge HTL | 2345 | 0.0039 |
| 64 | `SE.Max Jet Investment Hit Rate:SE.PY sensi multiplier[Jet]` | interaction | `SE.Max Jet Investment Hit Rate` | 1/year | 0.05 | 0.3 | Starch Ethanol-to-Jet | 3125 | 0.0185 |
| 65 | `WW.Mature Industry Rate of Return as PCT[ManureToHTL]:WW.initial indices of Commercial Maturity[ManureToHTL]` | interaction | `WW.Mature Industry Rate of Return as PCT[ManureToHTL]` | %/yr | 5.0 | 15.0 | Manure HTL | 918 | 0.0028 |
| 66 | `CHC.initial indices of Commercial Maturity[Biochem]` | identity | `CHC.initial indices of Commercial Maturity[Biochem]` | unitless | 0.0 | 0.2 | Cellulosic Biochem | 956 | 0.0057 |
| 67 | `WW.ORNOOC sensi multiplier[ManureToHTL]` | identity | `WW.ORNOOC sensi multiplier[ManureToHTL]` | unitless | 0.75 | 1.25 | Manure HTL | 1036 | 0.0180 |
| 68 | `WW.initial indices of Commercial Maturity[ManureToHTL]` | identity | `WW.initial indices of Commercial Maturity[ManureToHTL]` | Unitless | 0.0 | 0.2 | Manure HTL | 988 | 0.0022 |
| 69 | `WW.PY sensi multiplier[ManureToHTL]:WW.Policy Duration[Price,ManureToHTL]` | interaction | `WW.PY sensi multiplier[ManureToHTL]` | unitless | 0.75 | 1.25 | Manure HTL | 1918 | 0.0049 |
| 70 | `CHC.initial indices of Commercial Maturity[Biochem]:CHC.FCI  sensi multiplier[Biochem]` | interaction | `CHC.initial indices of Commercial Maturity[Biochem]` | unitless | 0.0 | 0.2 | Cellulosic Biochem | 1095 | 0.0036 |
| 71 | `inverse_CHC.Mature Industry Rate of Return as PCT[Brownfield]` | inverse | `CHC.Mature Industry Rate of Return as PCT[Brownfield]` | %/yr | 5.0 | 15.0 | Cellulosic Thermochem (Brownfield) | 3448 | 0.0073 |
| 72 | `inverse_SE.PY sensi multiplier[Jet]` | inverse | `SE.PY sensi multiplier[Jet]` | unitless | 0.75 | 1.25 | Starch Ethanol-to-Jet | 1415 | 0.0192 |
| 73 | `AHC.Mature Industry Rate of Return as PCT[HTL]` | identity | `AHC.Mature Industry Rate of Return as PCT[HTL]` | %/yr | 5.0 | 15.0 | Algal HTL | 493 | 0.0046 |
| 74 | `CHC.Mature Industry Rate of Return as PCT[Biochem]_squared` | quadratic | `CHC.Mature Industry Rate of Return as PCT[Biochem]` | %/yr | 5.0 | 15.0 | Cellulosic Biochem | 626 | 0.0055 |
| 75 | `inverse_CHC.FCI  sensi multiplier[Thermochem]` | inverse | `CHC.FCI  sensi multiplier[Thermochem]` | unitless | 0.75 | 1.25 | Cellulosic Thermochem | 3102 | 0.0159 |
| 76 | `CHC.FCI  sensi multiplier[Brownfield]` | identity | `CHC.FCI  sensi multiplier[Brownfield]` | unitless | 0.75 | 1.25 | Cellulosic Thermochem (Brownfield) | 606 | 0.0119 |
| 77 | `SE.Mature Industry Rate of Return as PCT[Jet]` | identity | `SE.Mature Industry Rate of Return as PCT[Jet]` | %/yr | 5.0 | 15.0 | Starch Ethanol-to-Jet | 2443 | 0.0058 |
| 78 | `WW.Mature Industry Rate of Return as PCT[ManureToHTL]` | identity | `WW.Mature Industry Rate of Return as PCT[ManureToHTL]` | %/yr | 5.0 | 15.0 | Manure HTL | 1702 | 0.0136 |
| 79 | `WW.FCI  sensi multiplier[ManureToHTL]` | identity | `WW.FCI  sensi multiplier[ManureToHTL]` | unitless | 0.75 | 1.25 | Manure HTL | 850 | 0.0079 |
| 80 | `CHC.PY sensi multiplier[Brownfield]` | identity | `CHC.PY sensi multiplier[Brownfield]` | unitless | 0.75 | 1.25 | Cellulosic Thermochem (Brownfield) | 1697 | 0.0187 |
| 81 | `SE.ORNOOC sensi multiplier[Jet]` | identity | `SE.ORNOOC sensi multiplier[Jet]` | unitless | 0.75 | 1.25 | Starch Ethanol-to-Jet | 3454 | 0.0072 |
| 82 | `AHC.initial indices of Commercial Maturity[HTL]:WW.initial indices of Commercial Maturity[SludgeToHTL]` | interaction | `AHC.initial indices of Commercial Maturity[HTL]` | unitless | 0.0 | 0.2 | Algal HTL | 4589 | 0.0025 |
| 83 | `AHC.Mature Industry Rate of Return as PCT[HEFA]` | identity | `AHC.Mature Industry Rate of Return as PCT[HEFA]` | %/yr | 5.0 | 15.0 | Algal HEFA | 1131 | 0.0031 |
| 84 | `WW.Policy Duration[Price,ManureToHTL]` | identity | `WW.Policy Duration[Price,ManureToHTL]` | year | 18.0 | 36.0 | Manure HTL | 1128 | 0.0117 |
| 85 | `AHC.FCI  sensi multiplier[HTL]` | identity | `AHC.FCI  sensi multiplier[HTL]` | unitless | 0.75 | 1.25 | Algal HTL | 522 | 0.0066 |
| 86 | `CHC.progress ratios commercial[Thermochem]` | identity | `CHC.progress ratios commercial[Thermochem]` | 1/doubling | 0.65 | 0.85 | Cellulosic Thermochem | 2438 | 0.6684 |
| 87 | `inverse_WW.FCI  sensi multiplier[SludgeToHTL]` | inverse | `WW.FCI  sensi multiplier[SludgeToHTL]` | unitless | 0.75 | 1.25 | Sewage Sludge HTL | 831 | 0.0049 |
| 88 | `SE.FCI  sensi multiplier[Jet]` | identity | `SE.FCI  sensi multiplier[Jet]` | unitless | 0.75 | 1.25 | Starch Ethanol-to-Jet | 690 | 0.0069 |
| 89 | `SE.PY sensi multiplier[Jet]` | identity | `SE.PY sensi multiplier[Jet]` | unitless | 0.75 | 1.25 | Starch Ethanol-to-Jet | 1733 | 0.0145 |
| 90 | `AHC.FCI  sensi multiplier[HEFA]` | identity | `AHC.FCI  sensi multiplier[HEFA]` | unitless | 0.75 | 1.25 | Algal HEFA | 713 | 0.0066 |
| 91 | `OHC.ORNOOC sensi multiplier[HEFA]` | identity | `OHC.ORNOOC sensi multiplier[HEFA]` | unitless | 0.75 | 1.25 | Oilcrop HEFA | 2740 | 0.0080 |
| 92 | `CHC.progress ratios commercial[Thermochem]:OHC.progress ratios commercial[HEFA]` | interaction | `CHC.progress ratios commercial[Thermochem]` | 1/doubling | 0.65 | 0.85 | Cellulosic Thermochem | 1774 | 0.0508 |
| 93 | `WW.progress ratios commercial[ManureToHTL]` | identity | `WW.progress ratios commercial[ManureToHTL]` | 1/doubling | 0.65 | 0.85 | Manure HTL | 199 | 0.0536 |
| 94 | `OHC.ORNOOC sensi multiplier[HEFABrownfield]` | identity | `OHC.ORNOOC sensi multiplier[HEFABrownfield]` | unitless | 0.75 | 1.25 | Oilcrop HEFA (Brownfield) | 1363 | 0.0332 |
| 95 | `inverse_WW.ORNOOC sensi multiplier[ManureToHTL]` | inverse | `WW.ORNOOC sensi multiplier[ManureToHTL]` | unitless | 0.75 | 1.25 | Manure HTL | 954 | 0.0031 |
| 96 | `OHC.PY sensi multiplier[HEFABrownfield]:WW.PY sensi multiplier[ManureToHTL]` | interaction | `OHC.PY sensi multiplier[HEFABrownfield]` | unitless | 0.75 | 1.25 | Oilcrop HEFA (Brownfield) | 791 | 0.0030 |
| 97 | `CHC.progress ratios commercial[Brownfield]` | identity | `CHC.progress ratios commercial[Brownfield]` | 1/doubling | 0.65 | 0.85 | Cellulosic Thermochem (Brownfield) | 640 | 0.0500 |
| 98 | `CHC.Debt Interest Rate as pct[Thermochem]` | identity | `CHC.Debt Interest Rate as pct[Thermochem]` | %/yr | 5.0 | 12.0 | Cellulosic Thermochem | 2920 | 0.0027 |
| 99 | `SE.Max Jet Investment Hit Rate:OHC.progress ratios commercial[HEFA]` | interaction | `SE.Max Jet Investment Hit Rate` | 1/year | 0.05 | 0.3 | Starch Ethanol-to-Jet | 837 | 0.0029 |
| 100 | `SE.progress ratios commercial[Jet]_squared` | quadratic | `SE.progress ratios commercial[Jet]` | 1/doubling | 0.65 | 0.85 | Starch Ethanol-to-Jet | 2209 | 0.0781 |
| 101 | `CHC.ORNOOC sensi multiplier[Thermochem]` | identity | `CHC.ORNOOC sensi multiplier[Thermochem]` | unitless | 0.75 | 1.25 | Cellulosic Thermochem | 2475 | 0.0083 |
| 102 | `WW.PY sensi multiplier[SludgeToHTL]:CHC.FCI  sensi multiplier[Brownfield]` | interaction | `WW.PY sensi multiplier[SludgeToHTL]` | unitless | 0.75 | 1.25 | Sewage Sludge HTL | 454 | 0.0029 |
| 103 | `inverse_WW.ORNOOC sensi multiplier[SludgeToHTL]` | inverse | `WW.ORNOOC sensi multiplier[SludgeToHTL]` | unitless | 0.75 | 1.25 | Sewage Sludge HTL | 681 | 0.0048 |
| 104 | `OHC.Policy Duration[Price,HEFA]` | identity | `OHC.Policy Duration[Price,HEFA]` | year | 18.0 | 36.0 | Oilcrop HEFA | 770 | 0.0023 |
| 105 | `CHC.FCI  sensi multiplier[Biochem]` | identity | `CHC.FCI  sensi multiplier[Biochem]` | unitless | 0.75 | 1.25 | Cellulosic Biochem | 881 | 0.0069 |
| 106 | `log1p_OHC.Mature Industry Rate of Return as PCT[HEFA]` | log1p | `OHC.Mature Industry Rate of Return as PCT[HEFA]` | %/yr | 5.0 | 15.0 | Oilcrop HEFA | 686 | 0.0073 |
| 107 | `OHC.PY sensi multiplier[HEFABrownfield]:OHC.ORNOOC sensi multiplier[HEFABrownfield]` | interaction | `OHC.PY sensi multiplier[HEFABrownfield]` | unitless | 0.75 | 1.25 | Oilcrop HEFA (Brownfield) | 1428 | 0.0156 |
| 108 | `inverse_AHC.FCI  sensi multiplier[HTL]` | inverse | `AHC.FCI  sensi multiplier[HTL]` | unitless | 0.75 | 1.25 | Algal HTL | 382 | 0.0031 |
| 109 | `OHC.ORNOOC sensi multiplier[HEFABrownfield]:SE.progress ratios commercial[Jet]` | interaction | `OHC.ORNOOC sensi multiplier[HEFABrownfield]` | unitless | 0.75 | 1.25 | Oilcrop HEFA (Brownfield) | 442 | 0.0095 |
| 110 | `SE.Policy Duration[Price,Jet]` | identity | `SE.Policy Duration[Price,Jet]` | year | 18.0 | 36.0 | Starch Ethanol-to-Jet | 1496 | 0.0179 |
| 111 | `CHC.PY sensi multiplier[Biochem]` | identity | `CHC.PY sensi multiplier[Biochem]` | unitless | 0.75 | 1.25 | Cellulosic Biochem | 607 | 0.0053 |
| 112 | `OHC.PY sensi multiplier[HEFABrownfield]:CHC.progress ratios commercial[Brownfield]` | interaction | `OHC.PY sensi multiplier[HEFABrownfield]` | unitless | 0.75 | 1.25 | Oilcrop HEFA (Brownfield) | 504 | 0.0083 |
| 113 | `inverse_OHC.progress ratios commercial[HEFABrownfield]` | inverse | `OHC.progress ratios commercial[HEFABrownfield]` | 1/doubling | 0.65 | 0.85 | Oilcrop HEFA (Brownfield) | 522 | 0.0285 |
| 114 | `CHC.Policy Duration[Price,Thermochem]` | identity | `CHC.Policy Duration[Price,Thermochem]` | year | 18.0 | 36.0 | Cellulosic Thermochem | 1399 | 0.0214 |
| 115 | `OHC.progress ratios commercial[HEFABrownfield]` | identity | `OHC.progress ratios commercial[HEFABrownfield]` | 1/doubling | 0.65 | 0.85 | Oilcrop HEFA (Brownfield) | 456 | 0.0291 |
| 116 | `CHC.Mature Industry Rate of Return as PCT[Brownfield]:SE.progress ratios commercial[Jet]` | interaction | `CHC.Mature Industry Rate of Return as PCT[Brownfield]` | %/yr | 5.0 | 15.0 | Cellulosic Thermochem (Brownfield) | 508 | 0.0035 |
| 117 | `OHC.Policy Duration[Price,HEFABrownfield]` | identity | `OHC.Policy Duration[Price,HEFABrownfield]` | year | 18.0 | 36.0 | Oilcrop HEFA (Brownfield) | 402 | 0.0031 |
| 118 | `OHC.progress ratios commercial[HEFA]:CHC.Policy Duration[Price,Thermochem]` | interaction | `OHC.progress ratios commercial[HEFA]` | 1/doubling | 0.65 | 0.85 | Oilcrop HEFA | 357 | 0.0050 |
| 119 | `CHC.FCI  sensi multiplier[Thermochem]:CHC.Policy Duration[Price,Thermochem]` | interaction | `CHC.FCI  sensi multiplier[Thermochem]` | unitless | 0.75 | 1.25 | Cellulosic Thermochem | 530 | 0.0020 |
| 120 | `inverse_OHC.progress ratios commercial[HEFA]` | inverse | `OHC.progress ratios commercial[HEFA]` | 1/doubling | 0.65 | 0.85 | Oilcrop HEFA | 1743 | 0.0712 |
| 121 | `CHC.PY sensi multiplier[Brownfield]:CHC.ORNOOC sensi multiplier[Thermochem]` | interaction | `CHC.PY sensi multiplier[Brownfield]` | unitless | 0.75 | 1.25 | Cellulosic Thermochem (Brownfield) | 1168 | 0.0051 |
| 122 | `inverse_OHC.ORNOOC sensi multiplier[HEFABrownfield]` | inverse | `OHC.ORNOOC sensi multiplier[HEFABrownfield]` | unitless | 0.75 | 1.25 | Oilcrop HEFA (Brownfield) | 203 | 0.0020 |
| 123 | `sqrt_CHC.progress ratios commercial[Thermochem]` | sqrt | `CHC.progress ratios commercial[Thermochem]` | 1/doubling | 0.65 | 0.85 | Cellulosic Thermochem | 2355 | 1.3094 |
| 124 | `WW.progress ratios commercial[SludgeToHTL]:CHC.Policy Duration[Price,Thermochem]` | interaction | `WW.progress ratios commercial[SludgeToHTL]` | 1/doubling | 0.65 | 0.85 | Sewage Sludge HTL | 328 | 0.0064 |
| 125 | `SE.progress ratios commercial[Jet]` | identity | `SE.progress ratios commercial[Jet]` | 1/doubling | 0.65 | 0.85 | Starch Ethanol-to-Jet | 2753 | 0.2004 |
| 126 | `inverse_CHC.progress ratios commercial[Brownfield]` | inverse | `CHC.progress ratios commercial[Brownfield]` | 1/doubling | 0.65 | 0.85 | Cellulosic Thermochem (Brownfield) | 673 | 0.0404 |
| 127 | `CHC.FCI  sensi multiplier[Biochem]:OHC.ORNOOC sensi multiplier[HEFABrownfield]` | interaction | `CHC.FCI  sensi multiplier[Biochem]` | unitless | 0.75 | 1.25 | Cellulosic Biochem | 503 | 0.0036 |
| 128 | `SE.Policy Duration[Price,Jet]_squared` | quadratic | `SE.Policy Duration[Price,Jet]` | year | 18.0 | 36.0 | Starch Ethanol-to-Jet | 1341 | 0.0052 |
| 129 | `CHC.Debt Interest Rate as pct[Biochem]` | identity | `CHC.Debt Interest Rate as pct[Biochem]` | %/yr | 5.0 | 12.0 | Cellulosic Biochem | 493 | 0.0025 |
| 130 | `inverse_AHC.FCI  sensi multiplier[HEFA]` | inverse | `AHC.FCI  sensi multiplier[HEFA]` | unitless | 0.75 | 1.25 | Algal HEFA | 543 | 0.0026 |
| 131 | `WW.progress ratios commercial[ManureToHTL]_squared` | quadratic | `WW.progress ratios commercial[ManureToHTL]` | 1/doubling | 0.65 | 0.85 | Manure HTL | 285 | 0.0188 |

## How to use this table

1. **Reading the coefficient matrix:** column at index `i` of the coefficient matrix corresponds to the feature at row `i` of this table.
2. **Reading a coefficient value:** the raw-scale coefficient maps to the base input in its native units; the standardized coefficient maps to the base input rescaled by its training-partition mean and standard deviation (see `x_standardization.csv`, `y_standardization.csv`).
3. **Interaction columns:** the product `x_a * x_b` is computed AFTER any per-side transformation (e.g. `quadratic_X:Y` = `X^2 * Y`).
4. **Unit conventions:** any unitless input has `units = 'unitless'`. Interactions and transformed inputs inherit the product/composition of their constituent units; the raw coefficient value carries the inverse of those units to recover the output unit.
