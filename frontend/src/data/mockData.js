/**
 * Mock data for hotels, ground transport, meals, and per diems
 * by city and traveler level. Used as fallback when APIs are unavailable.
 */

export const hotelRates = {
  NYC: { junior: 150, mid: 220, senior: 320, executive: 500 },
  LON: { junior: 140, mid: 200, senior: 300, executive: 480 },
  PAR: { junior: 130, mid: 190, senior: 280, executive: 450 },
  TYO: { junior: 120, mid: 180, senior: 260, executive: 420 },
  SIN: { junior: 140, mid: 210, senior: 310, executive: 490 },
  DXB: { junior: 110, mid: 170, senior: 250, executive: 400 },
  LAX: { junior: 130, mid: 190, senior: 280, executive: 450 },
  BER: { junior: 100, mid: 160, senior: 240, executive: 390 },
  SYD: { junior: 120, mid: 180, senior: 270, executive: 430 },
  HKG: { junior: 130, mid: 200, senior: 290, executive: 460 },
}

export const groundTransportDaily = {
  NYC: { junior: 35, mid: 50, senior: 70, executive: 120 },
  LON: { junior: 30, mid: 45, senior: 65, executive: 110 },
  PAR: { junior: 28, mid: 42, senior: 60, executive: 100 },
  TYO: { junior: 32, mid: 48, senior: 68, executive: 115 },
  SIN: { junior: 25, mid: 38, senior: 55, executive: 95 },
  DXB: { junior: 22, mid: 35, senior: 50, executive: 90 },
  LAX: { junior: 28, mid: 42, senior: 62, executive: 105 },
  BER: { junior: 24, mid: 36, senior: 52, executive: 92 },
  SYD: { junior: 26, mid: 40, senior: 58, executive: 98 },
  HKG: { junior: 27, mid: 41, senior: 59, executive: 102 },
}

export const mealsPerDiemDaily = {
  NYC: { junior: 55, mid: 80, senior: 110, executive: 170 },
  LON: { junior: 50, mid: 75, senior: 105, executive: 160 },
  PAR: { junior: 48, mid: 72, senior: 100, executive: 155 },
  TYO: { junior: 45, mid: 68, senior: 95, executive: 150 },
  SIN: { junior: 52, mid: 78, senior: 108, executive: 165 },
  DXB: { junior: 40, mid: 62, senior: 88, executive: 140 },
  LAX: { junior: 50, mid: 76, senior: 106, executive: 162 },
  BER: { junior: 42, mid: 64, senior: 90, executive: 145 },
  SYD: { junior: 46, mid: 70, senior: 98, executive: 152 },
  HKG: { junior: 48, mid: 74, senior: 104, executive: 158 },
}

export const miscellaneousDaily = {
  junior: 20,
  mid: 35,
  senior: 50,
  executive: 80,
}

export const cityMultiplier = {
  NYC: 1.5,
  LON: 1.4,
  PAR: 1.35,
  TYO: 1.3,
  SIN: 1.4,
  DXB: 1.2,
  LAX: 1.35,
  BER: 1.2,
  SYD: 1.3,
  HKG: 1.35,
}

export const defaultCity = 'NYC'
export const defaultLevel = 'mid'
