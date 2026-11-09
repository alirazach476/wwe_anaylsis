import { initials } from "../assets/assetManifest";
import { fighterAvatarUrl, inferFighterGender, type FighterGender } from "../assets/wrestlerGender";

export function WrestlerPortrait({
  name,
  size = 88,
  gender,
  matchContext,
  showInitials = true,
  showGenderBadge = true,
}: {
  name?: string | null;
  size?: number;
  gender?: FighterGender;
  matchContext?: { matchResult?: string | null; championshipLabel?: string | null; matchType?: string | null };
  showInitials?: boolean;
  showGenderBadge?: boolean;
}) {
  const resolved = gender || inferFighterGender(name, matchContext);
  const avatar = fighterAvatarUrl(resolved);
  const label = resolved === "female" ? "Woman" : "Man";

  return (
    <div
      className={`portrait fighter-portrait fighter-${resolved}`}
      style={{ width: size, height: size }}
      title={`${name || "Unknown"} · ${label}`}
      data-gender={resolved}
    >
      <img src={avatar} alt={`${label} wrestler`} className="fighter-avatar-img" />
      {showInitials ? <span className="fighter-initials">{initials(name)}</span> : null}
      {showGenderBadge ? (
        <span className={`fighter-gender-badge fighter-gender-${resolved}`} aria-hidden>
          {label}
        </span>
      ) : null}
    </div>
  );
}
