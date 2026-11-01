// Other forecasters' chamber odds, hand-entered with the date each one was read at its source (Max, 2026-10-29:
// "comparison and strip"; "If I can show different election models aside from my bet, wouldn't that be more impressive?").
// None publishes an API. Refresh these at every release, newest reading first. Undertow's own rows are never written here:
// FieldNotes reads them from the sealed simulation.
export type FieldRow = { name: string; house: number | null; senate: number | null; houseSeats?: string; senateSeats?: string; asOf: string; url: string; note?: string };
export const FIELD: FieldRow[] = [
  { name: 'The Economist', house: 0.94, senate: 0.54, houseSeats: '236', senateSeats: '51', asOf: '2026-11-01', url: 'https://www.economist.com/interactive/2026/us-midterms/prediction-model/house' },
  { name: 'Kalshi', house: 0.93, senate: 0.71, asOf: '2026-11-01', url: 'https://kalshi.com/category/politics/midterms', note: 'a market, not a model' },
  { name: 'Decision Desk HQ', house: 0.83, senate: 0.62, houseSeats: '241', senateSeats: '52', asOf: '2026-11-01', url: 'https://votes.decisiondeskhq.com/forecast/2026/house' },
  { name: 'Silver Bulletin', house: 0.95, senate: 0.764, senateSeats: '52', asOf: '2026-11-01', url: 'https://www.natesilver.net/p/nate-silver-2026-midterm-election-polls-model', note: 'paywalled; Senate figure from Oct 22 via Newsweek' },
  { name: 'Split Ticket', house: 0.92, senate: 0.73, houseSeats: '239', senateSeats: '53', asOf: '2026-10-31', url: 'https://x.com/lxeagle17/status/2116581431287873682', note: 'via the model author’s post' },
  { name: 'Cook Political Report', house: null, senate: null, houseSeats: '222 to 240', senateSeats: '7 toss-ups', asOf: '2026-10-30', url: 'https://www.cookpolitical.com/ratings/house-race-ratings', note: 'ratings only' },
];
