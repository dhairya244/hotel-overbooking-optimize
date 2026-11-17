# AI benchmark result

Output of `python ai_benchmark/run.py`, pasted unedited. Run on 17 November 2026 from this branch, with the code exactly as the AI wrote it.

```
=== Scored set ===
  raw rows                     119,390
  dropped: 0-night stays           715
  dropped: negative adr              1
  dropped: extreme adr (> 1,000)       1
  dropped: no guests               110
  scored rows                  118,563
  train 48,747 | choose 29,307 | proof 40,509

=== Non Refund bookings (train): cancellation rate ===
                            rate  bookings
hotel        deposit_type                 
City Hotel   No Deposit    0.272     25095
             Non Refund    0.998      6342
             Refundable    0.000         5
Resort Hotel No Deposit    0.206     16044
             Non Refund    0.950      1151
             Refundable    0.073       110

=== Choose period: model calibration (accuracy deliberately not reported) ===
                    model  log_loss  brier  night_mean_err  night_MAE
                logit/all    0.5223 0.1713            1.04       7.95
logit/no_special_requests    0.5318 0.1770            0.05       6.98
                  hgb/all    0.5459 0.1832           -6.21       8.54
  hgb/no_special_requests    0.5436 0.1846           -5.23       7.73
             segment_rate    0.5783 0.1841           -3.09       6.21

=== Choose period: each rule at its chosen buffer (ceiling 10 per 1,000) ===
                                                                                                    rule        hotel  cost_eur  empty_rooms  walked_guests  walks_per_1000  ceiling_met  nights
                            flat m={'City Hotel': np.int64(20), 'Resort Hotel': np.int64(4)} (per hotel)   City Hotel 1,231,929         3663            104            8.79         True     184
                            flat m={'City Hotel': np.int64(20), 'Resort Hotel': np.int64(4)} (per hotel) Resort Hotel   733,842         1212             79           11.98        False     184
                            flat m={'City Hotel': np.int64(20), 'Resort Hotel': np.int64(4)} (per hotel)        Total 1,965,771         4875            183            9.93         True     368
                logit/all z={'City Hotel': np.float64(5.2), 'Resort Hotel': np.float64(1.2)} (per hotel)        Total 1,599,634         4357            183            9.93         True     368
logit/no_special_requests z={'City Hotel': np.float64(3.5), 'Resort Hotel': np.float64(1.2)} (per hotel)        Total 1,460,691         3694            177            9.61         True     368
                  hgb/all z={'City Hotel': np.float64(1.8), 'Resort Hotel': np.float64(0.3)} (per hotel)        Total 1,617,501         4010            178            9.66         True     368
  hgb/no_special_requests z={'City Hotel': np.float64(1.3), 'Resort Hotel': np.float64(0.5)} (per hotel)        Total 1,441,326         3472            183            9.93         True     368
             segment_rate z={'City Hotel': np.float64(1.4), 'Resort Hotel': np.float64(1.0)} (per hotel)        Total 1,429,803         3105            178            9.66         True     368

Selected on choose: hgb/no_special_requests, buffer z={'City Hotel': np.float64(1.3), 'Resort Hotel': np.float64(0.5)} (per hotel); flat rule margin m={'City Hotel': np.int64(20), 'Resort Hotel': np.int64(4)} (per hotel). Flat choose cost EUR 1,965,771.

====================================================================================================
PROOF PERIOD: arrivals 1 Jan - 31 Aug 2017 (run once; settings frozen from choose)
====================================================================================================
Flat rate (train+choose): City Hotel 0.415, Resort Hotel 0.266
                                rule        hotel  cost_eur  empty_rooms  walked_guests  walks_per_1000  ceiling_met  nights
                  Flat rule (client)   City Hotel 1,969,801         5308             70            4.45         True     243
                  Flat rule (client) Resort Hotel 1,207,283         1795            134           14.79        False     243
                  Flat rule (client)        Total 3,177,085         7103            204            8.23         True     486
Model rule (hgb/no_special_requests)   City Hotel   543,627          247           1543           98.16        False     243
Model rule (hgb/no_special_requests) Resort Hotel   327,624          270            579           63.91        False     243
Model rule (hgb/no_special_requests)        Total   871,251          517           2122           85.64        False     486
                   Segment-rate rule   City Hotel   940,622         2343            110            7.00         True     243
                   Segment-rate rule Resort Hotel 1,140,943         1618             99           10.93        False     243
                   Segment-rate rule        Total 2,081,565         3961            209            8.43         True     486
                    Oversell nothing   City Hotel 4,320,007        11677              0            0.00         True     243
                    Oversell nothing Resort Hotel 2,409,574         4053              0            0.00         True     243
                    Oversell nothing        Total 6,729,581        15730              0            0.00         True     486
    Perfect foresight (unattainable)   City Hotel         0            0              0            0.00         True     243
    Perfect foresight (unattainable) Resort Hotel         0            0              0            0.00         True     243
    Perfect foresight (unattainable)        Total         0            0              0            0.00         True     486

Model calibration on proof:
                  model  log_loss  brier  night_mean_err  night_MAE
hgb/no_special_requests    0.5124 0.1748            7.49       8.35
           segment_rate    0.5610 0.1876           -2.60       5.99

Saving against the flat rule (proof):
  EUR 2,305,833  (72.6% of flat-rule cost)
  empty rooms 7,103 -> 517 (+6,586 fewer)
  walked guests 204 -> 2,122; walks per 1,000 8.23 -> 85.64 (ceiling 10)

Walks per 1,000 by month (proof):
  month  flat_walks_per_1000  model_walks_per_1000  flat_cost_eur  model_cost_eur
2017-01                21.24                 49.98         212433           67585
2017-02                10.76                 67.46         160602           71104
2017-03                19.01                141.32         219129          148532
2017-04                 2.51                100.31         437910          109327
2017-05                 5.67                 83.00         475317          123701
2017-06                 4.07                 83.28         519204          117074
2017-07                 2.72                 63.97         548575          114283
2017-08                 3.55                 84.49         603914          119646

Oversell table, 18-31 Aug 2017 (28 rows; final book treated as known):
       hotel      night  bookings_on_book  expected_cancellations  buffer_rooms  oversell_rooms  flat_rule_oversell  stay_value_eur
  City Hotel 2017-08-18               121                    62.0           6.7              55                  30           466.0
  City Hotel 2017-08-19               122                    65.7           6.2              59                  30           423.0
  City Hotel 2017-08-20               101                    46.5           6.2              40                  21           545.0
  City Hotel 2017-08-21                94                    46.5           5.9              40                  19           491.0
  City Hotel 2017-08-22                60                    28.4           4.7              23                   4           457.0
  City Hotel 2017-08-23                85                    39.0           5.7              33                  15           437.0
  City Hotel 2017-08-24                91                    44.0           5.9              38                  17           401.0
  City Hotel 2017-08-25               139                    51.3           6.7              44                  37           321.0
  City Hotel 2017-08-26               101                    43.1           6.0              37                  21           463.0
  City Hotel 2017-08-27               106                    48.5           6.4              42                  24           348.0
  City Hotel 2017-08-28               133                    55.1           7.1              47                  35           482.0
  City Hotel 2017-08-29                90                    50.7           5.5              45                  17           432.0
  City Hotel 2017-08-30                47                    23.1           4.2              18                   0           482.0
  City Hotel 2017-08-31                79                    36.4           5.3              31                  12           461.0
Resort Hotel 2017-08-18                60                    25.1           1.7              23                  11           880.0
Resort Hotel 2017-08-19                66                    28.9           1.8              27                  13          1249.0
Resort Hotel 2017-08-20                57                    26.8           1.7              25                  11          1209.0
Resort Hotel 2017-08-21                65                    28.1           1.9              26                  13          1080.0
Resort Hotel 2017-08-22                38                    15.4           1.4              13                   6           994.0
Resort Hotel 2017-08-23                40                    16.8           1.5              15                   6          1076.0
Resort Hotel 2017-08-24                65                    31.2           1.6              29                  13          1006.0
Resort Hotel 2017-08-25                52                    22.5           1.6              20                   9           893.0
Resort Hotel 2017-08-26                65                    28.1           1.9              26                  13          1200.0
Resort Hotel 2017-08-27                67                    25.4           1.8              23                  13           844.0
Resort Hotel 2017-08-28                78                    34.9           2.1              32                  16          1027.0
Resort Hotel 2017-08-29                35                    14.7           1.3              13                   5           991.0
Resort Hotel 2017-08-30                41                    18.5           1.5              17                   6           749.0
Resort Hotel 2017-08-31                55                    20.3           1.6              18                  10           764.0

Wrote ai_benchmark/oversell_table_2017-08-18_to_31.csv
```
