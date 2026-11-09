import { Link } from "react-router-dom";
import type { ReactNode, MouseEvent } from "react";
import { useWrestlerIndex } from "../state/WrestlerIndex";
import { cleanWrestlerName } from "../utils/wrestlerNames";

export function WrestlerNameLink({
  name,
  wrestlerId,
  className,
  children,
  stopPropagation = true,
}: {
  name?: string | null;
  wrestlerId?: string | null;
  className?: string;
  children?: ReactNode;
  stopPropagation?: boolean;
}) {
  const { resolveId, resolveName } = useWrestlerIndex();
  const display = resolveName(name) || cleanWrestlerName(name) || String(name || "—");
  const id = resolveId(name, wrestlerId);

  if (!id || display === "—" || display === "TBA" || display === "Unknown") {
    return <span className={className}>{children ?? display}</span>;
  }

  return (
    <Link
      to={`/wrestlers/${id}`}
      className={`wrestler-name-link${className ? ` ${className}` : ""}`}
      title={`Open ${display}`}
      onClick={(e: MouseEvent) => {
        if (stopPropagation) e.stopPropagation();
      }}
    >
      {children ?? display}
    </Link>
  );
}
