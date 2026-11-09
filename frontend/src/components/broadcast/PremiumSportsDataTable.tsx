import { Fragment, ReactNode, useMemo, useState } from "react";

export type PstColumn<T> = {
  key: string;
  header: string;
  sortable?: boolean;
  primary?: boolean;
  render?: (row: T) => ReactNode;
  sortValue?: (row: T) => string | number | null | undefined;
  width?: string;
};

export type PstVariant =
  | "results"
  | "wrestlers"
  | "reigns"
  | "history"
  | "rumble"
  | "attendance"
  | "yearly"
  | "changes"
  | "teams";

type Props<T> = {
  title: string;
  variant?: PstVariant;
  columns: PstColumn<T>[];
  rows: T[];
  rowKey: (row: T, index: number) => string;
  searchPlaceholder?: string;
  searchFilter?: (row: T, q: string) => boolean;
  pageSize?: number;
  isWinnerRow?: (row: T) => boolean;
  expandable?: (row: T) => ReactNode | null;
  emptyMessage?: string;
  toolbarExtra?: ReactNode;
};

export function PremiumSportsDataTable<T = any>({
  title,
  variant = "results",
  columns,
  rows,
  rowKey,
  searchPlaceholder = "Search…",
  searchFilter,
  pageSize = 25,
  isWinnerRow,
  expandable,
  emptyMessage = "No rows available.",
  toolbarExtra,
}: Props<T>) {
  const [q, setQ] = useState("");
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");
  const [page, setPage] = useState(0);
  const [open, setOpen] = useState<Record<string, boolean>>({});

  const filtered = useMemo(() => {
    let list = rows;
    if (q.trim() && searchFilter) {
      const needle = q.trim().toLowerCase();
      list = list.filter((r) => searchFilter(r, needle));
    }
    if (sortKey) {
      const col = columns.find((c) => c.key === sortKey);
      list = [...list].sort((a, b) => {
        const av = col?.sortValue?.(a) ?? (a as any)[sortKey];
        const bv = col?.sortValue?.(b) ?? (b as any)[sortKey];
        const an = av == null ? "" : av;
        const bn = bv == null ? "" : bv;
        if (typeof an === "number" && typeof bn === "number") {
          return sortDir === "asc" ? an - bn : bn - an;
        }
        return sortDir === "asc"
          ? String(an).localeCompare(String(bn))
          : String(bn).localeCompare(String(an));
      });
    }
    return list;
  }, [rows, q, searchFilter, sortKey, sortDir, columns]);

  const pageCount = Math.max(1, Math.ceil(filtered.length / pageSize));
  const safePage = Math.min(page, pageCount - 1);
  const pageRows = filtered.slice(safePage * pageSize, safePage * pageSize + pageSize);

  function toggleSort(key: string, sortable?: boolean) {
    if (!sortable) return;
    if (sortKey === key) setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    else {
      setSortKey(key);
      setSortDir("asc");
    }
  }

  return (
    <div className="pst" data-variant={variant}>
      <div className="pst-toolbar">
        <h3 className="pst-title">{title}</h3>
        {searchFilter ? (
          <input
            value={q}
            onChange={(e) => {
              setQ(e.target.value);
              setPage(0);
            }}
            placeholder={searchPlaceholder}
            aria-label="Search table"
          />
        ) : null}
        {toolbarExtra}
      </div>
      {!filtered.length ? (
        <div className="bc-empty" style={{ margin: 16, border: "none" }}>
          <h4>No data</h4>
          <p>{emptyMessage}</p>
        </div>
      ) : (
        <>
          <div className="pst-scroll">
            <table>
              <thead>
                <tr>
                  {columns.map((c) => (
                    <th
                      key={c.key}
                      className={sortKey === c.key ? "sorted" : undefined}
                      style={c.width ? { width: c.width } : undefined}
                      onClick={() => toggleSort(c.key, c.sortable !== false)}
                    >
                      {c.header}
                      {sortKey === c.key ? (
                        <span className="sort-ind">{sortDir === "asc" ? "▲" : "▼"}</span>
                      ) : c.sortable !== false ? (
                        <span className="sort-ind">↕</span>
                      ) : null}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {pageRows.map((row, i) => {
                  const key = rowKey(row, safePage * pageSize + i);
                  const detail = expandable?.(row);
                  const isOpen = open[key];
                  return (
                    <Fragment key={key}>
                      <tr
                        className={`${isWinnerRow?.(row) ? "is-winner" : ""}${isOpen ? " expanded" : ""}`}
                        onClick={
                          detail
                            ? () => setOpen((s) => ({ ...s, [key]: !s[key] }))
                            : undefined
                        }
                        style={detail ? { cursor: "pointer" } : undefined}
                      >
                        {columns.map((c) => (
                          <td key={c.key} style={c.primary ? { fontWeight: 600 } : undefined}>
                            {c.render ? c.render(row) : String((row as any)[c.key] ?? "—")}
                          </td>
                        ))}
                      </tr>
                      {detail && isOpen ? (
                        <tr>
                          <td colSpan={columns.length}>
                            <div className="pst-detail">{detail}</div>
                          </td>
                        </tr>
                      ) : null}
                    </Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
          <div className="pst-pager">
            <span>
              {filtered.length} rows · page {safePage + 1}/{pageCount}
            </span>
            <div style={{ display: "flex", gap: 8 }}>
              <button type="button" disabled={safePage <= 0} onClick={() => setPage((p) => Math.max(0, p - 1))}>
                Prev
              </button>
              <button
                type="button"
                disabled={safePage >= pageCount - 1}
                onClick={() => setPage((p) => Math.min(pageCount - 1, p + 1))}
              >
                Next
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
