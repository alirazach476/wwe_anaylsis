import { useState } from "react";
import { BRAND } from "../assets/assetManifest";

export function BrandLogo({
  size = 46,
  className = "brand-logo",
}: {
  size?: number;
  className?: string;
}) {
  // Official WWE web logo (PNG) first; SVG / mark only as fallbacks
  const [src, setSrc] = useState(BRAND.logoPng);
  const [step, setStep] = useState(0);

  return (
    <img
      src={src}
      alt="WWE"
      width={size}
      height={size}
      className={`${className} brand-logo-contrast`}
      onError={() => {
        if (step === 0) {
          setSrc(BRAND.logoSvg);
          setStep(1);
        } else if (step === 1) {
          setSrc(BRAND.logoMark);
          setStep(2);
        }
      }}
    />
  );
}
