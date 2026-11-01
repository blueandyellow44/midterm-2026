// The deterministic grader for one eval case: pure, so the known-bad answers can be proven in the unit suite.
// A case passes only when every expectation it names holds; the evidence names which one failed.
//
// expect: { says?: string | string[]   regex (i) the answer must match (every one, when a list)
//           never_says?: string        regex (i) the answer must not match
//           not_only?: string          the answer must not consist of this word alone
//           unsaid_ok?: true           the answer may say the page does not say (the default fails that on a says case,
//                                      because a stray match in an admission of silence is not the page making a fact plain)
//           judge?: string }           a yes/no question for the judge; yes fails. Run only after the checks pass.

const UNSAID = /(does not|doesn't|didn't|did not|not|never) (explicitly |directly |clearly )?(say|state|mention|specify|address|give|provide|describe|cover|explain|indicate|tell|show|include)|not (stated|mentioned|specified|given|provided|addressed|described|covered|explained|shown|included)|no (mention|information|indication|explanation)/i;

export function grade(c, answer) {
  const e = c.expect;
  const evidence = [];
  const a = String(answer ?? '');
  if (!a.trim()) evidence.push('no answer');
  if (e.says && !e.unsaid_ok && UNSAID.test(a)) evidence.push('answer says the page does not say');
  for (const s of Array.isArray(e.says) ? e.says : e.says ? [e.says] : []) if (!new RegExp(s, 'i').test(a)) evidence.push(`answer does not match /${s}/i`);
  if (e.never_says && new RegExp(e.never_says, 'i').test(a)) evidence.push(`answer matches /${e.never_says}/i`);
  if (e.not_only && new RegExp(`^\\W*${e.not_only}\\W*$`, 'i').test(a.trim())) evidence.push(`answer is only "${e.not_only}"`);
  return { pass: evidence.length === 0, evidence };
}

export function validateCases(cases) {
  const ids = new Set();
  for (const c of cases) {
    if (!c.id || !c.page || !c.ask || !c.expect) throw new Error(`case ${JSON.stringify(c).slice(0, 80)} lacks id, page, ask or expect`);
    if (ids.has(c.id)) throw new Error(`duplicate case id ${c.id}`);
    ids.add(c.id);
    if (!Object.keys(c.expect).length) throw new Error(`case ${c.id} checks nothing`);
  }
}
