/** Sample dominant colors from an event logo image to drive page theme. */

export type LogoPalette = {
  primary: string;
  accent: string;
  secondary: string;
  glow: string;
  background: string;
  panel: string;
};

function rgbToHex(r: number, g: number, b: number) {
  return `#${[r, g, b].map((v) => Math.max(0, Math.min(255, Math.round(v))).toString(16).padStart(2, "0")).join("")}`;
}

function luminance(r: number, g: number, b: number) {
  return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255;
}

function saturateHex(hex: string, amount = 1.15) {
  const m = hex.match(/^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i);
  if (!m) return hex;
  let r = parseInt(m[1], 16);
  let g = parseInt(m[2], 16);
  let b = parseInt(m[3], 16);
  const avg = (r + g + b) / 3;
  r = Math.min(255, avg + (r - avg) * amount);
  g = Math.min(255, avg + (g - avg) * amount);
  b = Math.min(255, avg + (b - avg) * amount);
  return rgbToHex(r, g, b);
}

function mix(hex: string, toward: string, t: number) {
  const parse = (h: string) => {
    const m = h.match(/^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i);
    if (!m) return [0, 0, 0];
    return [parseInt(m[1], 16), parseInt(m[2], 16), parseInt(m[3], 16)];
  };
  const a = parse(hex);
  const b = parse(toward);
  return rgbToHex(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t);
}

export async function extractLogoPalette(src: string): Promise<LogoPalette | null> {
  try {
    const img = await new Promise<HTMLImageElement>((resolve, reject) => {
      const el = new Image();
      el.crossOrigin = "anonymous";
      el.onload = () => resolve(el);
      el.onerror = () => reject(new Error("logo load failed"));
      el.src = src;
    });

    const canvas = document.createElement("canvas");
    const size = 48;
    canvas.width = size;
    canvas.height = size;
    const ctx = canvas.getContext("2d", { willReadFrequently: true });
    if (!ctx) return null;
    ctx.drawImage(img, 0, 0, size, size);
    const { data } = ctx.getImageData(0, 0, size, size);

    type Bucket = { r: number; g: number; b: number; n: number; score: number };
    const buckets = new Map<string, Bucket>();

    for (let i = 0; i < data.length; i += 4) {
      const a = data[i + 3];
      if (a < 140) continue;
      const r = data[i];
      const g = data[i + 1];
      const b = data[i + 2];
      const lum = luminance(r, g, b);
      // Skip near-black / near-white chrome
      if (lum < 0.08 || lum > 0.92) continue;
      const sat = Math.max(r, g, b) - Math.min(r, g, b);
      if (sat < 28) continue;
      const key = `${Math.round(r / 24)}_${Math.round(g / 24)}_${Math.round(b / 24)}`;
      const cur = buckets.get(key) || { r: 0, g: 0, b: 0, n: 0, score: 0 };
      cur.r += r;
      cur.g += g;
      cur.b += b;
      cur.n += 1;
      cur.score += sat * (0.65 + lum);
      buckets.set(key, cur);
    }

    const ranked = [...buckets.values()]
      .map((x) => ({
        r: x.r / x.n,
        g: x.g / x.n,
        b: x.b / x.n,
        n: x.n,
        score: x.score / x.n,
      }))
      .sort((a, b) => b.score * Math.sqrt(b.n) - a.score * Math.sqrt(a.n));

    if (!ranked.length) return null;

    const primaryRgb = ranked[0];
    const accentRgb =
      ranked.find((c) => {
        const dr = c.r - primaryRgb.r;
        const dg = c.g - primaryRgb.g;
        const db = c.b - primaryRgb.b;
        return Math.sqrt(dr * dr + dg * dg + db * db) > 55;
      }) || ranked[Math.min(1, ranked.length - 1)];

    const primary = saturateHex(rgbToHex(primaryRgb.r, primaryRgb.g, primaryRgb.b), 1.25);
    const accent = saturateHex(rgbToHex(accentRgb.r, accentRgb.g, accentRgb.b), 1.1);
    const secondary = mix(primary, "#050506", 0.88);
    const glow = `color-mix(in srgb, ${primary} 45%, transparent)`;
    const background = `radial-gradient(ellipse at 30% 0%, color-mix(in srgb, ${primary} 38%, #0a0a0b) 0%, #070708 52%), linear-gradient(160deg, ${secondary}, #030304)`;
    const panel = `color-mix(in srgb, ${secondary} 82%, rgba(0,0,0,0.55))`;

    return { primary, accent, secondary, glow, background, panel };
  } catch {
    return null;
  }
}
