# Provenance

Vendored verbatim (byte-for-byte, git-blob-SHA verified against upstream) from:

- Source: https://github.com/shadcn-ui/ui/tree/main/skills/shadcn
- Raw base: https://raw.githubusercontent.com/shadcn-ui/ui/main/skills/shadcn/
- Fetched: 2026-07-19
- Upstream ref: `main` branch at fetch time

No files in this directory were modified after download (SKILL.md's YAML
frontmatter format doesn't tolerate an inline provenance comment, hence this
sibling file instead). To refresh, re-fetch every file listed below from the
same raw base and re-verify with `git hash-object`.

| File | git blob SHA-1 (verified at fetch) |
| --- | --- |
| `SKILL.md` | `8c01af929563a687f691ccc7f4eeacb6b3c09d1c` |
| `cli.md` | `8a1d1958710902e2d38a3dd03d00aa09ab165dfe` |
| `customization.md` | `16954f56b158da368923e539b332746aa702bdac` |
| `mcp.md` | `6539ddaa2d0bc9e9d1fdf07658e1b0955136b721` |
| `registry.md` | `5369468bbe43126379161a403a53717ee86e2d9b` |
| `agents/openai.yml` | `ab636da86b5ee5b8721b0575af67faa88e4bf838` |
| `assets/shadcn-small.png` | `547154b97f2298335159c23eec1dac0d147a1246` |
| `assets/shadcn.png` | `b7b6814acc25073e5f48099b1fd3f70c47bfb1c3` |
| `evals/evals.json` | `c1b7bdd3102949f1617a4209ff5b285bc737166d` |
| `rules/base-vs-radix.md` | `c1ed7d111a0195cab801d2b3d38dee3aee0b8e10` |
| `rules/chat.md` | `8ce62fe4bf4e46ae5f4ca30037053a8baf30dfa6` |
| `rules/composition.md` | `0654245abaf4142a75ce1cf830c0691001d781c8` |
| `rules/forms.md` | `f451e2f7bc17d9c5738691931964744a568ea5d6` |
| `rules/icons.md` | `bba8102f01ef9fd9bd7ce2adc73e562869d5d09e` |
| `rules/styling.md` | `fe75197968ea5237afa15db44970b22e1db5b914` |

This skill is bundled so every product scaffolded from
`templates/saas-monorepo` ships with shadcn/ui agent guidance out of the box
(component search/add/fix/style rules), matching the vendored components in
`packages/ui/src/components/ui/`. It is not maintained by this repo — to
pick up upstream changes, re-run the fetch above and diff.
