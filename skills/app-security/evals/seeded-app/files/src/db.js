// In-memory store with a parameterized query shim. Values are never
// interpolated into the statement text.
const tables = { users: [], workspaces: [], members: [], docs: [], shares: [], jobs: [] }

export function query(sql, params = []) {
  const [, table, column] = sql.match(/FROM (\w+) WHERE (\w+) = \?/) ?? []
  if (!table) throw new Error('unsupported statement')
  return tables[table].filter((row) => row[column] === params[0])
}

export function insert(table, row) { tables[table].push(row); return row }
export function remove(table, column, value) {
  tables[table] = tables[table].filter((row) => row[column] !== value)
}
export function all(table) { return tables[table] }
