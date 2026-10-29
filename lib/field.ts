// Other forecasters' chamber odds, hand-entered with the date each one was read at its source (Max, 2026-10-29:
// "comparison and strip"; "If I can show different election models aside from my bet, wouldn't that be more impressive?").
// None publishes an API. Refresh these at every release, newest reading first. Undertow's own rows are never written here:
// FieldNotes reads them from the sealed simulation.
export type FieldRow = { name: string; house: number | null; senate: number | null; houseSeats?: string; senateSeats?: string; asOf: string; url: string; note?: string };
export const FIELD: FieldRow[] = [
  { name: 'The Economist', house: 0.95, senate: 0.50, houseSeats: '236', asOf: '2026-10-29', url: 'https://www.economist.com/interactive/2026/us-midterms/prediction-model/house' },
  { name: 'Kalshi', house: 0.92, senate: 0.68, asOf: '2026-10-29', url: 'https://kalshi.com/category/politics/midterms', note: 'a market, not a model' },
  { name: 'Decision Desk HQ', house: 0.80, senate: 0.60, houseSeats: '238', senateSeats: '52', asOf: '2026-10-29', url: 'https://votes.decisiondeskhq.com/forecast/2026/house' },
  { name: 'Silver Bulletin', house: 0.931, senate: 0.748, houseSeats: '239', senateSeats: '52', asOf: '2026-10-08', url: 'https://www.natesilver.net/p/nate-silver-2026-midterm-election-polls-model', note: 'paywalled; via Newsweek' },
  { name: 'Split Ticket', house: 0.89, senate: 0.65, asOf: '2026-10-14', url: 'https://www.theargumentmag.com/p/split-ticket-2026-midterms-model', note: 'via Channel 4 News' },
  { name: 'Cook Political Report', house: null, senate: null, houseSeats: '220 to 237', senateSeats: '6 toss-ups', asOf: '2026-10-23', url: 'https://www.cookpolitical.com/ratings/house-race-ratings', note: 'ratings only' },
];
