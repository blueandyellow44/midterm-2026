// Email sign-up for the post-election grade. Plain HTML form posted to Buttondown (Max's LITMUS list, tagged
// "undertow-<placement>"), same mechanics as the LITMUS site: no script, opens Buttondown's confirm page in a new tab.
const ACTION = 'https://buttondown.com/api/emails/embed-subscribe/sheahan';

export function Signup({ placement }: { placement: string }) {
  return <section className="signup" aria-label="Get the grade by email">
    <p className="signup-title">Get the grade</p>
    <p className="signup-pitch">I will email you how the bet did once the results are in. It goes out on my LITMUS weekly letter, so you will get that too, and you can leave any time.</p>
    <form action={ACTION} method="post" target="_blank" rel="noopener" className="signup-form">
      <label htmlFor={`signup-${placement}`} className="sr-only">Email address</label>
      <input id={`signup-${placement}`} type="email" name="email" required autoComplete="email" placeholder="Email address"/>
      <input type="hidden" name="tag" value={`undertow-${placement}`}/>
      <button type="submit">Send me the grade</button>
    </form>
    <p className="signup-note">Free. Sent by Buttondown, which holds your address.</p>
  </section>;
}
