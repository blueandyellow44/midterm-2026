import type { Metadata } from 'next';
import { PageTitle } from '@/components/UI';
import { Ballot } from '@/components/Ballot';
import { ballotRaces, BALLOT_PDF, BALLOT_RATING_DATES } from '@/lib/ballot';
import { topScore } from '@/lib/ballot-code';
import { pageShare } from '@/lib/format';

const DESCRIPTION = 'An election night ballot for November 3: pick who wins the Senate and the House, and every Senate and governor race Cook does not rate safe, then score your friends as the AP calls them.';
export const metadata: Metadata = { title: 'Ballot', description: DESCRIPTION, ...pageShare('/ballot/', 'Election night ballot', DESCRIPTION) };

// Election night ballot (Max, 2026-11-03: "move the phone version to the Undertow site"; races and scoring by his
// answers the same day). The print sheet in public/ballot/ carries the same picks.
export default function BallotPage() {
  const races = ballotRaces();
  return <>
    <PageTitle kicker="Election night · November 3 · A game, not a wager" title="Election night ballot."><p>Pick who wins the Senate and the House, and the winner of every Senate and governor race Cook does not call safe. Copy your picks into the group chat before polls close. Whoever keeps score pastes everyone’s picks into Standings and taps each winner as the AP calls it.</p></PageTitle>
    <Ballot races={races} top={topScore(races)} pdf={BALLOT_PDF} ratingDates={BALLOT_RATING_DATES}/>
  </>;
}
