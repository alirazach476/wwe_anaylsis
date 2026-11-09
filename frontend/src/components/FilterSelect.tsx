import { useEffect, useId, useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";

type Option = { value: string; label: string };

export function FilterSelect({
  value,
  onChange,
  options,
  placeholder,
  ariaLabel,
}: {
  value: string;
  onChange: (value: string) => void;
  options: Option[];
  placeholder: string;
  ariaLabel: string;
}) {
  const id = useId();
  const btnRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState(false);
  const [pos, setPos] = useState({ top: 0, left: 0, width: 220 });

  const selected = options.find((o) => o.value === value);
  const label = selected?.label || placeholder;

  function place() {
    const el = btnRef.current;
    if (!el) return;
    const r = el.getBoundingClientRect();
    const width = Math.max(r.width, 220);
    const maxH = Math.min(320, window.innerHeight - 24);
    let top = r.bottom + 6;
    if (top + maxH > window.innerHeight - 8) {
      top = Math.max(8, r.top - maxH - 6);
    }
    let left = r.left;
    if (left + width > window.innerWidth - 8) left = Math.max(8, window.innerWidth - width - 8);
    setPos({ top, left, width });
  }

  useLayoutEffect(() => {
    if (!open) return;
    place();
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onScroll = () => place();
    const onResize = () => place();
    const onPointer = (e: MouseEvent) => {
      const t = e.target as Node;
      if (btnRef.current?.contains(t) || menuRef.current?.contains(t)) return;
      setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    window.addEventListener("scroll", onScroll, true);
    window.addEventListener("resize", onResize);
    document.addEventListener("mousedown", onPointer);
    document.addEventListener("keydown", onKey);
    return () => {
      window.removeEventListener("scroll", onScroll, true);
      window.removeEventListener("resize", onResize);
      document.removeEventListener("mousedown", onPointer);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  return (
    <>
      <button
        ref={btnRef}
        id={id}
        type="button"
        className={`filter-select-trigger${open ? " open" : ""}${value ? " has-value" : ""}`}
        aria-label={ariaLabel}
        aria-haspopup="listbox"
        aria-expanded={open}
        onClick={() => setOpen((o) => !o)}
      >
        <span>{label}</span>
        <span className="filter-select-caret" aria-hidden>
          ▾
        </span>
      </button>
      {open
        ? createPortal(
            <div
              ref={menuRef}
              className="filter-select-menu"
              role="listbox"
              aria-labelledby={id}
              style={{
                top: pos.top,
                left: pos.left,
                width: pos.width,
                maxHeight: Math.min(320, window.innerHeight - 24),
              }}
            >
              <button
                type="button"
                role="option"
                className={`filter-select-option${!value ? " active" : ""}`}
                aria-selected={!value}
                onClick={() => {
                  onChange("");
                  setOpen(false);
                }}
              >
                {placeholder}
              </button>
              {options.map((o) => (
                <button
                  key={o.value}
                  type="button"
                  role="option"
                  className={`filter-select-option${value === o.value ? " active" : ""}`}
                  aria-selected={value === o.value}
                  onClick={() => {
                    onChange(o.value);
                    setOpen(false);
                  }}
                >
                  {o.label}
                </button>
              ))}
            </div>,
            document.body
          )
        : null}
    </>
  );
}
