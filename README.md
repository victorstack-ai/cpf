# CPF — Compact Prompt Format

Token-efficient instruction encoding for LLMs. Converts verbose English prompts into a compressed notation that LLMs understand natively — 30-50% fewer tokens, zero runtime dependencies.

## Why

LLM prompts are full of repeated English grammar ("If a module exists, then recommend it. Do NOT reinvent the wheel."). CPF replaces that grammar with operators and abbreviations that LLMs already understand, cutting token usage without losing meaning.

```
English (~120 tokens):
- Before coding a custom solution, always check if a maintained module or plugin exists.
- If a maintained module/plugin exists: recommend it. Link to it. Do NOT reinvent the wheel.
- If a module exists but is abandoned (no updates in 12+ months): code a custom solution and explain why.
- If no module/plugin exists: code from scratch. State that none was found.

CPF (~35 tokens):
@R:mod-first
?mnt(mod|plg)exists->recommend+link;!!reinvent
?exists+abd(12m+)->code+explain-why
?!exists->code-scratch+state-none-found
```

## Format

### Document structure

```
CPF|v1
M|<doc-id>|<title>|<source>|<timestamp>
---
@SIGIL:block-id
compressed content lines
```

### Operators

| Symbol | Meaning | Replaces |
|--------|---------|----------|
| `?` | If/When | "If", "When" |
| `?!` | Unless | "If not", "Unless" |
| `->` | Then | "then", "do" |
| `;` | Else | "otherwise" |
| `+` | And | "and", "also" |
| `\|` | Or | "or" |
| `!!` | Never | "do NOT", "never" |
| `*` | Must | "must", "important" |
| `::` | Defined as | "means", "is" |
| `@>` | See/Refer | "see", "refer to" |

### Block sigils

| Sigil | Type | Use |
|-------|------|-----|
| `@R:id` | Rule | Conditional rules, decision logic |
| `@P:id` | Priority | Ordered hierarchies |
| `@N:id` | Negation | "Do NOT" lists |
| `@S:id` | Sequence | Ordered steps |
| `@T:id` | Tone | Persona, voice, style |
| `@X:id` | Exact | Literal strings that MUST appear |
| `@Z:id` | Zone | Path/scope-based rules |
| `@C:id` | Constant | Reusable abbreviation definitions |
| `@B:id` | Blob | Heredoc passthrough (`<<`/`>>`) |

### Built-in abbreviations

`mod`=module, `plg`=plugin, `mnt`=maintained, `abd`=abandoned, `cfg`=config, `sec`=security, `perf`=performance, `dep`=dependency, `fn`=function, `svc`=service, `cch`=cache, `ctx`=context, `req`=require, `val`=validate, `san`=sanitize, `esc`=escape, `chk`=check, `doc`=documentation, `ver`=version, `upd`=update, `brk`=breaking, `depr`=deprecation, `impl`=implementation, `auth`=authentication, `perm`=permissions, `wp`=WordPress, `dp`=Drupal, `dx`=dev-experience, `stab`=stability

## Install

```bash
pip install -e .
```

## CLI

```bash
cpf encode persona.md -o persona.cpf          # English -> CPF
cpf decode persona.cpf -o persona_expanded.md  # CPF -> English
cpf validate persona.cpf                       # check correctness
cpf stats persona.cpf --original persona.md    # show token reduction %
```

## Python API

```python
from cpf.encoder import encode, encode_file
from cpf.decoder import decode
from cpf.validator import is_valid

# Encode
cpf_text = encode_file(Path("persona.md"))

# Decode
english = decode(cpf_text)

# Validate
assert is_valid(cpf_text)
```

## LLM preamble

When sending CPF-encoded instructions to an LLM, prepend a short legend so it can decode the notation:

```
<<CPF-LEGEND
?=if ?!=unless ->=then ;=else +=and |=or !!=never *=must ::=def @>=see
mod=module plg=plugin mnt=maintained abd=abandoned cfg=config sec=security ...
@R=rules @P=priorities @N=negation @S=sequence @T=tone @X=exact-literal @Z=zone
>>
```

The preamble costs ~80 tokens but saves 30-50% on the instruction blocks that follow.

## Tests

```bash
python3 -m pytest tests/ -v
```

## License

MIT
