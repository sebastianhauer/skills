// Commit-message rules, enforced by the commitlint hook in
// .pre-commit-config.yaml and by CI (commit-messages.yml) on every
// branch commit and on the PR title + body (the future squash commit).
// config-conventional supplies the 11-type type-enum and case rules;
// the overrides below add the house length limits (subject <= 70 so a
// squash PR title survives GitHub's ~72 truncation, body wrapped at 72).
// Lines containing URLs are exempt from all line-length rules;
// footer-max-line-length stays at the default 100 for non-URL trailers.
// defaultIgnores would silently skip merge messages, "fixup!"/"squash!"
// prefixes, and GitHub's auto revert-PR titles (Revert "..."), letting
// them land on master unvalidated -- disabled to match the old hook's
// --strict behavior. Reverts must use the revert: type; update fork
// branches by rebase, since a local git merge default message fails
// the hook (CI already skips merge commits via --no-merges).
export default {
  extends: ['@commitlint/config-conventional'],
  defaultIgnores: false,
  rules: {
    'header-max-length': [2, 'always', 70],
    'body-max-line-length': [2, 'always', 72],
  },
};
