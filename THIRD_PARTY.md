# Third-party dependency inventory
Runtime Python dependencies: none. CPython and the linked SQLite library are required platform components. No source, assets, or datasets from another repository are included.

The authoritative versions and installed licence metadata are recorded in
requirements-dev.lock and reports/DEPENDENCIES.json. Direct tools are setuptools,
build, pytest, coverage, Ruff, mypy, Bandit, pip-audit and PyYAML. Security tools
share the complete hash-locked development environment. requirements-test.lock is
a smaller constrained subset for pytest, YAML workflow parsing and packaging
requirement checks; it introduces no new runtime or development package.

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

## Version 0.2 tooling update
The generated requirements-dev.lock supersedes the original version list. It now includes
security/CI tooling and its transitive environment, all hash pinned. pytest was updated to
9.0.3 and setuptools to 84.1.0 in response to actual advisory findings. The new dependency
inventory records installed licence metadata for the resolved environment; missing metadata
is reported as unknown, not assumed permissive. No third-party packages are vendored into
the runtime wheel. Redistribution of the complete tooling environment requires separate
licence review. Scanner tooling adds maintenance dependencies, not runtime dependencies.
