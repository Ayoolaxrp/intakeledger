# Third-party dependency inventory
Runtime Python dependencies: none. CPython and the linked SQLite library are required platform components. No source, assets, or datasets from another repository are included.

The development lock pins these direct tools: setuptools 79.0.1, build 1.6.0, pytest 8.3.3, coverage 7.15.4, Ruff 0.6.5, and mypy 1.11.2. Their transitive dependencies are pinned separately in the lock. Local package metadata identifies setuptools as MIT, build as MIT, pytest as MIT, coverage as Apache-2.0, Ruff as MIT, and mypy as MIT. A machine-readable local inventory is generated during verification.

Security checks optionally install Bandit 1.9.4 under Apache-2.0 and pip-audit 2.10.1 under Apache-2.0. Official project pages were consulted on 2026-10-23. Their transitive packages resolve separately from the core development lock and are not a complete hash-locked environment.

This review checks dependency declarations and local package metadata, not every upstream file or every possible legal obligation. No dependencies are vendored or redistributed in the source archive. A future binary or container distribution needs review of the actual bundled interpreter, SQLite build, licences, and notices. No licence compatibility guarantee is made for an owner-selected project licence.

## Development licence details
| Package | Licence | Local evidence |
| --- | --- | --- |
| build | MIT | Distribution metadata |
| colorama | BSD-3-Clause | Installed LICENSE.txt reviewed, including its three redistribution conditions |
| coverage | Apache-2.0 | Distribution metadata |
| iniconfig | MIT | Distribution metadata |
| mypy | MIT | Distribution metadata |
| mypy-extensions | MIT | Distribution metadata |
| packaging | Apache-2.0 OR BSD-2-Clause | Distribution metadata |
| pluggy | MIT | Distribution metadata |
| pyproject-hooks | MIT | Installed LICENSE reviewed |
| pytest | MIT | Distribution metadata |
| Ruff | MIT | Distribution metadata |
| setuptools | MIT | Top-level installed LICENSE reviewed |
| typing-extensions | PSF-2.0 | Distribution metadata |

The inventory's unknown metadata fields are resolved by the licence-file review above. setuptools also contains vendored tools with separate notices, including an LGPL-3.0 autocommand component. The development lock is therefore not an assertion that every file inside installed tooling is MIT. Tooling is not copied into this repository or its wheel. Redistributing a whole development environment needs a separate review.
