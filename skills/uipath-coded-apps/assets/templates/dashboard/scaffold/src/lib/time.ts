// Relative time windows for dashboard queries, computed once at module load.
// Metric modules import the windows they need. Moved out of the build script's
// inline TIME_CONSTANTS splice so metric modules type-check in isolation.
export const NOW = new Date()
export const ONE_DAY_AGO = new Date(Date.now() - 86_400_000)
export const SEVEN_DAYS_AGO = new Date(Date.now() - 604_800_000)
export const THIRTY_DAYS_AGO = new Date(Date.now() - 2_592_000_000)
export const NINETY_DAYS_AGO = new Date(Date.now() - 7_776_000_000)
