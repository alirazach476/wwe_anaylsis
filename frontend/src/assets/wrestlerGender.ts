/** Heuristic gender for local fighter avatars (no invented roster facts). */

const WOMEN_NAMES = new Set(
  [
    "aj lee",
    "alexa bliss",
    "aliyah",
    "alundra blayze",
    "arianna grace",
    "asuka",
    "awesome kong",
    "azm",
    "bailey",
    "bayley",
    "becky lynch",
    "beth phoenix",
    "bianca belair",
    "blair davenport",
    "brie bella",
    "candice lerae",
    "carmella",
    "charlotte flair",
    "chelsea green",
    "chia",
    "chyna",
    "cora jade",
    "dakota kai",
    "dana brooke",
    "elektra lopez",
    "ember moon",
    "emma",
    "eva marie",
    "fallon henley",
    "gail kim",
    "gigi dolin",
    "giulia",
    "hikaru shida",
    "indy hartwell",
    "ivory",
    "ivy nile",
    "iyo sky",
    "ivyo sky",
    "jacy jayne",
    "jacqueline",
    "jade cargill",
    "jaida parker",
    "jazz",
    "jordynne grace",
    "jordan grace",
    "julia hart",
    "kairi sane",
    "karmen petrovic",
    "katana chance",
    "kayden carter",
    "kelani jordan",
    "kelly kelly",
    "lita",
    "liv morgan",
    "lola vice",
    "lyra valkyria",
    "lyra valkria",
    "mariah may",
    "maryse",
    "maxxine dupri",
    "maya yukihi",
    "mayu imazaki",
    "meiko satomura",
    "melina",
    "mercedes mone",
    "mercedes moné",
    "mia yim",
    "michelle mccool",
    "michin",
    "miss elizabeth",
    "momo watanabe",
    "naomi",
    "natalya",
    "nattie",
    "nia jax",
    "nikki bella",
    "nikki cross",
    "nikkita lyons",
    "nyla rose",
    "paige",
    "piper niven",
    "raquel rodriguez",
    "rhea ripley",
    "riho",
    "roxanne perez",
    "sasha banks",
    "sensational sherri",
    "shayna baszler",
    "shotzi",
    "skye blue",
    "sol ruca",
    "starlight kid",
    "statlander",
    "stephanie vaquer",
    "summer rae",
    "syuri",
    "tam nakano",
    "taynara conti",
    "thea hail",
    "thunder rosa",
    "tiffany stratton",
    "toni storm",
    "trish stratus",
    "utami hayashishita",
    "valentina fera",
    "valkyria",
    "victoria",
    "wendy choo",
    "wendi richter",
    "willow nightingale",
    "xia brookside",
    "zelina vega",
    "zoey stark",
    // brand / nickname forms
    "dirty dominik", // keep male via MEN override below — not listed as woman
  ]
    .filter((s) => s !== "dirty dominik")
    .map((s) => s.toLowerCase())
);

const WOMEN_FIRST_NAMES = new Set(
  [
    "alexa",
    "aliyah",
    "asuka",
    "bailey",
    "bayley",
    "becky",
    "beth",
    "bianca",
    "blair",
    "brie",
    "candice",
    "carmella",
    "charlotte",
    "chelsea",
    "chyna",
    "cora",
    "dakota",
    "dana",
    "elektra",
    "ember",
    "eva",
    "fallon",
    "gail",
    "gigi",
    "giulia",
    "indy",
    "ivory",
    "ivy",
    "iyo",
    "jacy",
    "jacqueline",
    "jade",
    "jaida",
    "jordynne",
    "julia",
    "kairi",
    "karmen",
    "katana",
    "kayden",
    "kelani",
    "kelly",
    "lita",
    "liv",
    "lola",
    "lyra",
    "mariah",
    "maryse",
    "maxxine",
    "melina",
    "mercedes",
    "mia",
    "michelle",
    "michin",
    "naomi",
    "natalya",
    "nattie",
    "nia",
    "nikki",
    "nikkita",
    "nyla",
    "paige",
    "piper",
    "raquel",
    "rhea",
    "roxanne",
    "sasha",
    "shayna",
    "shotzi",
    "skye",
    "sol",
    "stephanie",
    "summer",
    "thea",
    "tiffany",
    "toni",
    "trish",
    "wendy",
    "willow",
    "xia",
    "zelina",
    "zoey",
  ].map((s) => s.toLowerCase())
);

const WOMEN_TOKENS = [
  "women",
  "woman",
  "women's",
  "womens",
  "ladies",
  "divas",
  "diva",
  "queen",
  "empress",
  "valkyrie",
];

/** Explicit male overrides when first-name heuristic would collide. */
const MEN_NAMES = new Set(
  [
    "john cena",
    "randy orton",
    "roman reigns",
    "seth rollins",
    "brock lesnar",
    "triple h",
    "undertaker",
    "kane",
    "edge",
    "christian",
    "cm punk",
    "aj styles",
    "drew mcintyre",
    "gunther",
    "dominik mysterio",
    "dirty dominik mysterio",
    "rey mysterio",
    "eddie guerrero",
    "jeff hardy",
    "matt hardy",
    "shawn michaels",
    "stone cold steve austin",
    "the rock",
    "batista",
    "bobby lashley",
    "braun strowman",
    "kevin owens",
    "sami zayn",
    "finn balor",
    "damian priest",
    "la knight",
    "logan paul",
    "jey uso",
    "jimmy uso",
    "solo sikoa",
    "jacob fatu",
    "bron breakker",
    "cody rhodes",
  ].map((s) => s.toLowerCase())
);

export type FighterGender = "male" | "female";

function normalizePersonName(name?: string | null): string {
  return String(name || "")
    .toLowerCase()
    .replace(/[“”"'`]/g, "")
    .replace(/\[[^\]]*\]/g, " ")
    .replace(/\([^)]*\)/g, " ")
    .replace(/[)(]/g, " ")
    .replace(/^(?:the\s+|dirty\s+|and\s+)/, "")
    .replace(/\b(?:wwe|wwf|raw|smackdown|universal|world|united states|intercontinental|women'?s|men'?s)\s+champion\b/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

export function inferFighterGender(
  name?: string | null,
  context?: { matchResult?: string | null; championshipLabel?: string | null; matchType?: string | null }
): FighterGender {
  const cleaned = normalizePersonName(name);
  if (!cleaned) return "male";

  if (MEN_NAMES.has(cleaned)) return "male";
  for (const man of MEN_NAMES) {
    if (cleaned === man || cleaned.endsWith(` ${man}`)) return "male";
  }

  if (WOMEN_NAMES.has(cleaned)) return "female";
  for (const known of WOMEN_NAMES) {
    // Prefer containment of full known ring names inside scraped strings
    if (cleaned === known || cleaned.includes(known) || known.includes(cleaned)) return "female";
  }

  const parts = cleaned.split(" ").filter(Boolean);
  const first = parts[0] || "";
  const last = parts[parts.length - 1] || "";
  if (WOMEN_FIRST_NAMES.has(first)) return "female";
  // "Lynch", "Belair", "Flair" etc. alone rarely appear; keep first-name primary

  const ctx = `${context?.matchResult || ""} ${context?.championshipLabel || ""} ${context?.matchType || ""}`.toLowerCase();
  const womenCtx = WOMEN_TOKENS.some((t) => ctx.includes(t));
  const mensCtx = /\bmen'?s\b|\bmens\b/.test(ctx) && !womenCtx;
  if (womenCtx && !mensCtx) return "female";

  // Last-token fallback for multi-word women already covered by WOMEN_NAMES containment
  if (parts.length >= 2 && WOMEN_FIRST_NAMES.has(first) && last.length > 1) return "female";

  return "male";
}

/** Cache-bust so avatar art updates show immediately after redesign. */
const AVATAR_VER = "v2";

export function fighterAvatarUrl(gender: FighterGender): string {
  return gender === "female"
    ? `/branding/avatars/female-fighter.svg?${AVATAR_VER}`
    : `/branding/avatars/male-fighter.svg?${AVATAR_VER}`;
}
