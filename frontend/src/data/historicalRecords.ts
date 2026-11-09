/** Recognized WWE historical landmark records (curated “original” records). */

export type HistoricalRecord = {
  id: string;
  category: "Championships" | "Physical" | "Specials" | "Milestones";
  title: string;
  holder: string;
  value: string;
  detail: string;
  era?: string;
};

export const HISTORICAL_RECORDS: HistoricalRecord[] = [
  {
    id: "most-world-titles",
    category: "Championships",
    title: "Most world championship reigns",
    holder: "John Cena",
    value: "17",
    detail: "WWE-recognized world title reigns (WWE / World Heavyweight / Undisputed lineages).",
    era: "2005–present",
  },
  {
    id: "most-womens-world-titles",
    category: "Championships",
    title: "Most women’s world championship reigns",
    holder: "Charlotte Flair",
    value: "14",
    detail: "Record women’s world-title reigns across Raw, SmackDown, and Undisputed titles.",
    era: "2010s–present",
  },
  {
    id: "longest-universal-reign",
    category: "Championships",
    title: "Longest Universal Championship reign",
    holder: "Roman Reigns",
    value: "1,316 days",
    detail: "Historic Universal / Undisputed reign ending at WrestleMania XL (April 2024).",
    era: "2021–2024",
  },
  {
    id: "longest-wwe-reign-alltime",
    category: "Championships",
    title: "Longest WWE Championship reign (all-time)",
    holder: "Bruno Sammartino",
    value: "2,803 days",
    detail: "First WWWF/WWE Championship reign — longest singles world-title reign in company history.",
    era: "1963–1971",
  },
  {
    id: "shortest-wwe-reign",
    category: "Championships",
    title: "Shortest WWE Championship reign",
    holder: "André the Giant",
    value: "~45 seconds",
    detail: "Among the shortest recognized WWE Championship reigns in history.",
    era: "1988",
  },
  {
    id: "most-ic-reigns",
    category: "Championships",
    title: "Most Intercontinental Championship reigns",
    holder: "Chris Jericho",
    value: "9",
    detail: "All-time Intercontinental Championship reign record.",
    era: "1999–2010s",
  },
  {
    id: "most-us-reigns-modern",
    category: "Championships",
    title: "Most United States Championship reigns (WWE era leader)",
    holder: "John Cena",
    value: "5",
    detail: "Five-time United States Champion — a defining mid-card-to-main-event bridge record.",
    era: "2004–2010s",
  },
  {
    id: "longest-womens-sd-reign",
    category: "Championships",
    title: "Longest SmackDown Women’s Championship reign",
    holder: "Bayley",
    value: "380 days",
    detail: "Longest reign in SmackDown Women’s Championship history.",
    era: "2019–2020",
  },
  {
    id: "most-rumble-wins",
    category: "Specials",
    title: "Most Royal Rumble wins",
    holder: "Stone Cold Steve Austin",
    value: "3",
    detail: "Only Superstar with three Royal Rumble victories (1997, 1998, 2001).",
    era: "1997–2001",
  },
  {
    id: "undertaker-mania-streak",
    category: "Specials",
    title: "Longest WrestleMania winning streak",
    holder: "The Undertaker",
    value: "21–0",
    detail: "The Streak — undefeated at WrestleMania before Brock Lesnar ended it at XXX.",
    era: "1991–2013",
  },
  {
    id: "most-mitb-wins",
    category: "Specials",
    title: "Most Money in the Bank ladder match wins",
    holder: "CM Punk",
    value: "2",
    detail: "First to win MITB twice, including a same-night cash-in landmark.",
    era: "2008–2009",
  },
  {
    id: "heaviest",
    category: "Physical",
    title: "Heaviest billed WWE Champion",
    holder: "Yokozuna",
    value: "~568–600 lb",
    detail: "Billed among the heaviest world champions during his early-1990s title runs.",
    era: "1990s",
  },
  {
    id: "heaviest-andre",
    category: "Physical",
    title: "Heaviest iconic giant",
    holder: "André the Giant",
    value: "~520 lb",
    detail: "Billed weight that defined WWE’s giant archetype for decades.",
    era: "1970s–1980s",
  },
  {
    id: "lightest-mens",
    category: "Physical",
    title: "Lightest modern men’s world champion (billed)",
    holder: "Rey Mysterio",
    value: "~175 lb",
    detail: "One of the lightest men to capture WWE’s world championship spotlight.",
    era: "2000s–present",
  },
  {
    id: "lightest-womens",
    category: "Physical",
    title: "Lightest women’s championship standout (billed)",
    holder: "Alexa Bliss",
    value: "~102 lb",
    detail: "Among the lightest billed Superstars to dominate WWE’s women’s title scene.",
    era: "2010s–2020s",
  },
  {
    id: "youngest-wwe-champ",
    category: "Milestones",
    title: "Youngest WWE Champion (modern landmark)",
    holder: "Randy Orton",
    value: "24 years",
    detail: "Won the WWE Championship at age 24 — a modern-era youth landmark.",
    era: "2004",
  },
  {
    id: "longest-career-span-icon",
    category: "Milestones",
    title: "Longest iconic career span landmark",
    holder: "The Undertaker",
    value: "30 years",
    detail: "Three decades from debut to farewell — among WWE’s longest legendary careers.",
    era: "1990–2020",
  },
];

export const RECORD_CATEGORIES = ["Championships", "Physical", "Specials", "Milestones"] as const;
