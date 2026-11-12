**SYNTHETIC DATA — EXPERIMENTAL EVALUATION**

# Subgroup evaluation (test set — descriptive only)

## parts_cost
| Dimension | Group | n | MAE | RMSE | R² |
|---|---|---:|---:|---:|---:|
| repair_category | BATTERY | 113 | 41.6029 | 64.5752 | 0.9608 |
| repair_category | BODY | 92 | 52.0180 | 77.6069 | 0.9203 |
| repair_category | BRAKES | 205 | 19.4082 | 24.7519 | 0.6968 |
| repair_category | COOLING | 123 | 39.5154 | 61.2971 | 0.9660 |
| repair_category | ELECTRICAL | 142 | 41.7800 | 54.5755 | 0.8984 |
| repair_category | ENGINE | 150 | 132.2307 | 238.7336 | 0.9388 |
| repair_category | EXHAUST | 116 | 89.1082 | 151.7745 | 0.9417 |
| repair_category | FUEL | 99 | 46.9167 | 66.8021 | 0.9529 |
| repair_category | HVAC | 96 | 91.8754 | 121.8919 | 0.8789 |
| repair_category | STEERING | 99 | 54.0758 | 107.7699 | 0.9774 |
| repair_category | SUSPENSION | 134 | 31.9750 | 43.8941 | 0.9201 |
| repair_category | TRANSMISSION | 119 | 90.4554 | 165.9076 | 0.9619 |
| component | Battery system | 89 | 29.1814 | 38.1928 | 0.6055 |
| component | Body exterior | 92 | 52.0180 | 77.6069 | 0.9203 |
| component | Brake system | 205 | 19.4082 | 24.7519 | 0.6968 |
| component | Charging system | 97 | 60.3518 | 81.8083 | 0.8922 |
| component | Climate control | 56 | 120.9241 | 148.5695 | 0.6889 |
| component | Cooling system | 123 | 39.5154 | 61.2971 | 0.9660 |
| component | Engine assembly | 86 | 191.8805 | 309.3775 | 0.9016 |
| component | Engine cooling | 64 | 52.0762 | 70.4469 | 0.5643 |
| component | Exhaust system | 116 | 89.1082 | 151.7745 | 0.9417 |
| component | Fuel delivery | 51 | 76.0534 | 90.9254 | 0.7123 |
| component | Fuel system | 48 | 15.9591 | 20.4896 | 0.5293 |
| component | HVAC system | 40 | 51.2074 | 68.9656 | 0.5530 |
| component | Starting system | 69 | 31.6321 | 40.8506 | 0.5487 |
| component | Steering system | 99 | 54.0758 | 107.7699 | 0.9774 |
| component | Suspension system | 134 | 31.9750 | 43.8941 | 0.9201 |
| component | Transmission system | 119 | 90.4554 | 165.9076 | 0.9619 |
| repair_action | Repair | 614 | 23.5466 | 34.5587 | 0.9361 |
| repair_action | Replacement | 874 | 84.4843 | 147.7346 | 0.9485 |
| vehicle_age_group | (0, 3] | 722 | 59.6684 | 123.0400 | 0.9562 |
| vehicle_age_group | (3, 7] | 513 | 61.0390 | 114.3900 | 0.9623 |
| vehicle_age_group | (7, 12] | 253 | 54.9538 | 92.5254 | 0.9684 |

## labour_hours
| Dimension | Group | n | MAE | RMSE | R² |
|---|---|---:|---:|---:|---:|
| repair_category | BATTERY | 113 | 0.1422 | 0.2575 | 0.9752 |
| repair_category | BODY | 92 | 0.3594 | 0.4674 | 0.7987 |
| repair_category | BRAKES | 205 | 0.1300 | 0.1779 | 0.8955 |
| repair_category | COOLING | 123 | 0.2117 | 0.2925 | 0.9305 |
| repair_category | ELECTRICAL | 142 | 0.2144 | 0.2785 | 0.7932 |
| repair_category | ENGINE | 150 | 0.5264 | 0.7237 | 0.9588 |
| repair_category | EXHAUST | 116 | 0.2333 | 0.3194 | 0.9287 |
| repair_category | FUEL | 99 | 0.2857 | 0.3942 | 0.9167 |
| repair_category | HVAC | 96 | 0.4887 | 0.6505 | 0.8070 |
| repair_category | STEERING | 99 | 0.3188 | 0.5108 | 0.9727 |
| repair_category | SUSPENSION | 134 | 0.2448 | 0.3025 | 0.8082 |
| repair_category | TRANSMISSION | 119 | 0.4312 | 0.6368 | 0.9776 |
| component | Battery system | 89 | 0.0601 | 0.0717 | 0.6666 |
| component | Body exterior | 92 | 0.3594 | 0.4674 | 0.7987 |
| component | Brake system | 205 | 0.1300 | 0.1779 | 0.8955 |
| component | Charging system | 97 | 0.2812 | 0.3645 | 0.8698 |
| component | Climate control | 56 | 0.4774 | 0.6482 | 0.7035 |
| component | Cooling system | 123 | 0.2117 | 0.2925 | 0.9305 |
| component | Engine assembly | 86 | 0.7163 | 0.9095 | 0.8241 |
| component | Engine cooling | 64 | 0.2712 | 0.3407 | 0.7609 |
| component | Exhaust system | 116 | 0.2333 | 0.3194 | 0.9287 |
| component | Fuel delivery | 51 | 0.3781 | 0.4895 | 0.6918 |
| component | Fuel system | 48 | 0.1876 | 0.2567 | 0.7333 |
| component | HVAC system | 40 | 0.5044 | 0.6537 | 0.7729 |
| component | Starting system | 69 | 0.2013 | 0.2736 | 0.7843 |
| component | Steering system | 99 | 0.3188 | 0.5108 | 0.9727 |
| component | Suspension system | 134 | 0.2448 | 0.3025 | 0.8082 |
| component | Transmission system | 119 | 0.4312 | 0.6368 | 0.9776 |
| repair_action | Repair | 614 | 0.2408 | 0.3461 | 0.9759 |
| repair_action | Replacement | 874 | 0.3219 | 0.4958 | 0.9724 |
| vehicle_age_group | (0, 3] | 722 | 0.2852 | 0.4403 | 0.9752 |
| vehicle_age_group | (3, 7] | 513 | 0.2999 | 0.4525 | 0.9747 |
| vehicle_age_group | (7, 12] | 253 | 0.2744 | 0.4141 | 0.9673 |