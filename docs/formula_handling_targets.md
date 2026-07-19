# Formula handling targets

These dry-qualifying targets calibrate the physical grip envelope and gearbox.
They do not script vehicle speed or steer the player. Public Formula 1 timing
telemetry is sampled at low frequency, so speeds should be read as roughly
`+/- 5-10 km/h` and gears as `+/- 1`; flat-throttle classifications are the
stronger contract.

## Grip model

The Tidebreaker baseline is 1.87 g of mechanical lateral grip. At maximum
speed, its downforce raises the yaw-effective envelope to 4.80 g. The imported
track outlines are deliberately compact and some fast bends are consequently
tighter than their real counterparts, so the simulation applies a smooth,
corner-local calibration around the mapped Formula targets. The largest
current correction is 2.28x. It is based on the reference car so vehicle grip
differences remain intact, ramps in only as the car approaches the target
speed, and fades across the curb rather than carrying into the runoff. Slow
corners still require braking to reach the target gear and speed.

## Suzuka

Reference: [Max Verstappen's 2024 pole lap](https://www.formula1.com/en/video/onboard-max-verstappens-2024-pirelli-pole-position-award-lap-at-the-japanese-grand-prix.1795576994761470754), plus the [Mercedes 2024 circuit guide](https://www.mercedesamgf1.com/races/japanese-grand-prix-2024).

| Corner | Target | Gear | Throttle note |
|---|---:|---:|---|
| Turn 1 / Turn 2 | 261 -> 172 km/h | 7 -> 5 | Brake after initial turn-in |
| Esses | 240 -> 189 km/h | 6 -> 5 | Flowing partial-throttle sequence |
| Dunlop | 245 km/h | 6 | High speed |
| Degner 1 | 267 km/h | 7 | Full throttle |
| Degner 2 | 139 km/h | 4 | Brake |
| Hairpin | 74 km/h | 3 | Heavy brake |
| Spoon | 232 -> 168 km/h | 6 -> 5 | Late apex |
| 130R | 297 km/h minimum | 8 | Full throttle; approach near 320 km/h |
| Casio Triangle | 89 km/h | 3 | Heavy brake |

## Spa-Francorchamps

Reference: [2022 qualifying report](https://www.formula1.com/en/latest/article/verstappen-fastest-in-qualifying-but-sainz-set-to-start-on-pole-after.18uRqCjdY4iTx2s1CtiQ1m.18uRqCjdY4iTx2s1CtiQ1m) and [F1 technical analysis](https://www.formula1.com/en/latest/article/tech-tuesday-how-red-bull-engineered-the-rb18-to-dominate-at-spa.3QCa91D0rv2PNbjXx802Wz).

| Corner | Target | Gear | Throttle note |
|---|---:|---:|---|
| La Source | 77 km/h | 2 | Heavy brake |
| Eau Rouge / Raidillon | 302 km/h | 8 | Full throttle |
| Les Combes | 156 km/h | 4 | Brake |
| Bruxelles | 125 km/h | 4 | Trail brake |
| No Name | 208 km/h | 5 | Fast exit |
| Pouhon | 284 km/h | 7 | Full throttle on reference lap |
| Fagnes | 178-185 km/h | 5 | Brake |
| Campus | 160 km/h | 4 | Brake |
| Stavelot | 243 km/h | 6 | Accelerating |
| Blanchimont | 307 km/h | 8 | Full throttle |
| Bus Stop | 72 km/h | 2 | Heavy brake |

## Silverstone

Reference: [Max Verstappen's 2023 pole lap](https://www.formula1.com/en/latest/article/watch-ride-onboard-with-verstappen-at-silverstone-as-he-takes-his-fifth.1IHzD4zxRuZz1pKe6ndM0X).

| Corner | Target | Gear | Throttle note |
|---|---:|---:|---|
| Abbey / Farm | 295 / 293 km/h | 8 | Full throttle |
| Village | 113 km/h | 3 | Brake |
| The Loop | 94 km/h | 3 | Slow rotation |
| Brooklands | 156 km/h | 4 | Brake |
| Luffield | 114 km/h | 4 | Long exit |
| Woodcote | 259 km/h | 6 | Full throttle |
| Copse | 290 km/h | 8 | Full throttle |
| Maggotts / Becketts | 301 -> 226 km/h | 8 -> 6 | Fast direction changes |
| Stowe | 230 km/h | 6 | Brake |
| Vale | 99 km/h | 3 | Heavy brake |
| Club | 171 km/h | 4 | Accelerating |

## Monza

Reference: [Lando Norris's 2024 pole lap](https://www.formula1.com/en/video/onboard-lando-norris-2024-pirelli-pole-position-award-lap-at-the-italian-grand-prix.1808919989852209304/).

| Corner | Target | Gear | Throttle note |
|---|---:|---:|---|
| Rettifilo | 73 km/h | 2 | Heavy brake |
| Curva Grande | 294 km/h | 8 | Full throttle |
| Roggia | 113 km/h | 3 | Heavy brake |
| Lesmo 1 | 207 km/h | 5 | Brake |
| Lesmo 2 | 190 km/h | 5 | Brake |
| Ascari | 194 -> 235 km/h | 5 -> 6 | Accelerating through exit |
| Parabolica / Alboreto | 215 km/h | 5 | Long accelerating exit |

## Interlagos

Reference: [official 2023 qualifying results](https://www.formula1.com/en/results/2023/races/1224/brazil/qualifying).

| Corner | Target | Gear | Throttle note |
|---|---:|---:|---|
| Senna S | 109-111 km/h | 3 | Heavy brake |
| Curva do Sol | 228 km/h | 6 | Accelerating |
| Descida do Lago | 167 km/h | 4 | Brake |
| Ferradura | 226-231 km/h | 6 | High speed |
| Pinheirinho | 108 km/h | 3 | Brake |
| Bico de Pato | 88 km/h | 3 | Slowest corner |
| Mergulho | 206 km/h | 5 | Fast downhill |
| Juncao | 119 km/h | 3 | Critical uphill exit |
| Final sweep | 153 -> 312 km/h | 3 -> 8 | Full throttle |

The checked-in handling audit verifies 48 target/gear mappings through the
actual automatic transmission—accelerating into flat sections and braking into
the others. It also runs 48 target-speed lateral-dynamics checks and samples
720 points through their entry-apex-exit calibration windows. Suzuka 130R has a
full path-following vehicle test as well: eighth gear, no contact, and at least
285 km/h.
