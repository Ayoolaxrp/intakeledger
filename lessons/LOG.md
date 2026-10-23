# Engineering lessons
2026-10-23: Large parametrized byte fixtures produced pytest identifiers that exceeded Windows path limits. Explicit short test IDs fixed the fixture setup failures.

2026-10-23: SQLite internal-name filtering must use a literal underscore. A LIKE pattern treated the underscore as a wildcard and could ignore an unrelated table named sqliteXprivate. GLOB now uses the literal prefix, and a byte-for-byte preservation test protects the boundary.

2026-10-23: Installed tool metadata can omit a licence. Read the relevant installed licence file instead of assuming the missing field proves a missing licence.

2026-10-23: Owner explicitly disabled Ponytail for this project. Use the Atlas brief and keep delivery fast.
