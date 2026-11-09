import { BrandLogo } from "./BrandLogo";

export function LoadingScreen({ visible }: { visible: boolean }) {
  return (
    <div className={`loading-screen${visible ? "" : " hide"}`} aria-hidden={!visible}>
      <div className="loading-inner">
        <BrandLogo size={120} />
        <p>LEGACY ANALYTICS</p>
      </div>
    </div>
  );
}
