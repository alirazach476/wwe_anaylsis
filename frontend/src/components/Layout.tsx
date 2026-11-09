import { useEffect, useMemo, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { BRAND } from "../assets/assetManifest";
import { useEventTheme } from "../theme/EventThemeContext";
import { BrandLogo } from "./BrandLogo";
import { FilterBar } from "./FilterBar";
import { LoadingScreen } from "./LoadingScreen";

const links: { to: string; label: string; ico: string }[] = [
  { to: "/", label: "Home", ico: "◆" },
  { to: "/events", label: "All Events", ico: "▣" },
  { to: "/matches", label: "Match Center", ico: "⚔" },
  { to: "/wrestlers", label: "Wrestler Analytics", ico: "◎" },
  { to: "/championships", label: "Championship Analytics", ico: "★" },
  { to: "/global", label: "Global Analytics", ico: "◉" },
  { to: "/ml", label: "Machine Learning", ico: "Σ" },
  { to: "/timeline", label: "Historical Timeline", ico: "⋯" },
];

const titles: Record<string, string> = {
  "/": "Home",
  "/events": "Event Explorer",
  "/matches": "Match Center",
  "/wrestlers": "Wrestler Analytics",
  "/championships": "Championship Analytics",
  "/global": "Global Analytics",
  "/ml": "Machine Learning",
  "/timeline": "Historical Timeline",
};

export function Layout() {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [booting, setBooting] = useState(true);
  const [search, setSearch] = useState("");
  const location = useLocation();
  const { resetTheme } = useEventTheme();

  useEffect(() => {
    const t = window.setTimeout(() => setBooting(false), 900);
    return () => window.clearTimeout(t);
  }, []);

  useEffect(() => {
    setMobileOpen(false);
    if (!location.pathname.startsWith("/events/") && !location.pathname.startsWith("/series/")) resetTheme();
  }, [location.pathname, resetTheme]);

  const title = useMemo(() => {
    if (location.pathname.startsWith("/series/")) return "Event Series";
    if (location.pathname.startsWith("/events/")) return "Event Detail";
    if (location.pathname.startsWith("/wrestlers/")) return "Wrestler Profile";
    return titles[location.pathname] || BRAND.siteName;
  }, [location.pathname]);

  return (
    <>
      <LoadingScreen visible={booting} />
      <div className={`app-shell${collapsed ? " collapsed" : ""}`}>
        <aside className={`sidebar${mobileOpen ? " open" : ""}`}>
          <div className="brand-block">
            <BrandLogo />
            {!collapsed && (
              <div className="brand-copy">
                <h1>WWE</h1>
                <p>Legacy Analytics</p>
              </div>
            )}
          </div>
          <nav className="nav-list">
            {links.map((l) => (
              <NavLink
                key={l.to}
                to={l.to}
                end={l.to === "/"}
                className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
                title={l.label}
              >
                <span className="nav-ico">{l.ico}</span>
                {!collapsed && <span>{l.label}</span>}
              </NavLink>
            ))}
          </nav>
          {!collapsed && <div className="sidebar-foot">PLE dataset · 2000–2027</div>}
        </aside>
        <div className="main-column">
          <header className="topbar">
            <button className="icon-btn" type="button" onClick={() => setCollapsed((c) => !c)} aria-label="Toggle sidebar">
              ☰
            </button>
            <button
              className="icon-btn"
              type="button"
              onClick={() => setMobileOpen((o) => !o)}
              aria-label="Mobile nav"
              style={{ display: undefined }}
            >
              ▤
            </button>
            <h2>{title}</h2>
            <input
              className="search-field"
              placeholder="Search events & wrestlers…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && search.trim()) {
                  window.location.assign(`/events?q=${encodeURIComponent(search.trim())}`);
                }
              }}
            />
          </header>
          <div className="filter-strip">
            <FilterBar />
          </div>
          <div className="page">
            <Outlet />
          </div>
        </div>
      </div>
    </>
  );
}
