# Contract and command reference
A contract contains name, version, fields, and optional allow_extra. Unknown contract and field-specification properties are errors. Names match [a-z][a-z0-9_-]{0,63}. Versions are integers from 1 to 2147483647. Fields are named ASCII identifiers of at most 64 characters.

## Field rules
| Property | Meaning |
| --- | --- |
| type | string, integer, number, or boolean |
| required | Defaults to true. Missing values are invalid when true. |
| nullable | Defaults to false. Null values are allowed when true, independently of enum. |
| min, max | Inclusive bounds for integer or number fields. Booleans and non-finite numbers are invalid bounds. |
| min_length, max_length | Inclusive Unicode code-point lengths for strings, between 0 and 65536. |
| enum | Between 1 and 64 distinct non-null values of the field type. Bounds and lengths also apply. |

Contracts contain 1 to 64 fields. Definitions cannot replace an existing name/version with changed semantics. Canonicalization fills defaults and sorts fields. Redundant numeric representations are not a semantic-normalization guarantee. Register a new version for changed rules.

Numbers follow Python JSON numeric parsing. Use integer minor units or strings for money requiring exact decimal precision. Nested extra values may be retained only when allow_extra=true. No nested constraints exist.

## Input limits
Feeds use UTF-8 with LF or CRLF rows, at most 8 MiB and 10,000 physical rows, and at most 256 KiB per row excluding its terminator. A trailing terminator creates no extra row. Empty files fail. Blank physical rows are invalid. Contract files are at most 128 KiB. JSON nesting is at most depth 32. Duplicate keys, unpaired surrogates, invalid JSON, and non-finite numbers quarantine the affected row. Invalid UTF-8 or size limits reject the entire request before persistence.

## CLI
Global arguments --db and --verbose precede the command.
| Command | Result |
| --- | --- |
| init | Create or verify schema and return health |
| register FILE | Register contract definition |
| ingest FILE --source S --key K --contract C --version N | Persist a batch |
| replay ID --key K --contract C --version N | Persist a child batch |
| show ID | Batch metadata |
| rows ID [--include-payload] | Per-row lineage and issues |
| export ID | Accepted JSON objects, one per line |
| health | SQLite quick_check, foreign-key check, and counts |

Ingest and replay accept --max-invalid as an exact decimal or rational string from 0 to 1. Sources and keys contain 1 to 200 characters without controls. SQLite busy timeout defaults to 5 seconds and can be configured up to 30 seconds through the library.

Exit codes: 0 success, 2 invalid input or file/database failure, 3 identity conflict, 4 busy database, 5 rejected batch or blocked export, 130 keyboard interruption. Domain errors use a JSON error object on stderr. Help uses ordinary text. Batch ingestion that returns 5 still writes its rejected-batch audit record.
