import type { Metadata } from 'next';
import { PageTitle, Empty } from '@/components/UI';
import { Ballot } from '@/components/Ballot';
import { ballotRaces, BALLOT_PDF, BALLOT_RATING_DATES } from '@/lib/ballot';
import { topScore, siteCalls, mergeCalls } from '@/lib/ballot-code';
import { loadLive } from '@/lib/live';
import { loadCalls } from '@/lib/live-calls';
import { pageShare } from '@/lib/format';

const DESCRIPTION = 'An election night ballot for November 3: pick who wins the Senate and the House, and every Senate and governor race Cook does not rate safe, then score your friends as the AP calls them.';
export const metadata: Metadata = { title: 'Ballot', description: DESCRIPTION, ...pageShare('/ballot/', 'Election night ballot', DESCRIPTION) };

// Election night ballot (Max, 2026-11-03: "move the phone version to the Undertow site"; races and scoring by his
// answers the same day). The print sheet in public/ballot/ carries the same picks.
export default function BallotPage() {
  const races = ballotRaces();
  // Races Undertow has called fill in Standings on their own; the scorekeeper taps only the rest.
  // live/calls.json adds AP calls for races with no official count (NH, ME, WI and the untracked seats).
  const calls = races.length ? mergeCalls(siteCalls(races, loadLive().races), loadCalls(new Set(races.map(r => r.id)))) : {};
  return <>
    <PageTitle kicker="Election night · November 3 · A game, not a wager" title="Election night ballot."><p>Pick who wins the Senate and the House, and the winner of every Senate and governor race Cook does not call safe. Copy your picks into the group chat before polls close. Whoever keeps score pastes everyone’s picks into Standings. Races Undertow has called fill in from its results. The scorekeeper taps the rest as the AP calls them.</p></PageTitle>
    {races.length ? <Ballot races={races} calls={calls} top={topScore(races)} pdf={BALLOT_PDF} ratingDates={BALLOT_RATING_DATES}/>
      : <Empty title="The ballot is unavailable for this release.">This release carries no seat ratings, so there is no race list to pick from.</Empty>}
  </>;
}
