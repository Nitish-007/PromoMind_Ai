"use client";

import React, { useState, useRef, useEffect } from "react";
import { ChevronDown, Check } from "lucide-react";

export function CustomSelect({
  value,
  onChange,
  options = [],
  placeholder = "Select option...",
  className = "",
  disabled = false,
}) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef(null);

  // Normalize options: can be array of strings or array of { value, label, sublabel }
  const normalizedOptions = options.map((opt) => {
    if (typeof opt === "object" && opt !== null) {
      return {
        value: opt.value,
        label: opt.label || opt.value,
        sublabel: opt.sublabel || null,
      };
    }
    return { value: opt, label: opt, sublabel: null };
  });

  const selectedOption = normalizedOptions.find((opt) => opt.value === value);

  // Handle outside click
  useEffect(() => {
    function handleClickOutside(event) {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen]);

  // Handle keyboard navigation
  const handleKeyDown = (e) => {
    if (disabled) return;
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      setIsOpen((prev) => !prev);
    } else if (e.key === "Escape") {
      setIsOpen(false);
    } else if (e.key === "ArrowDown" && !isOpen) {
      e.preventDefault();
      setIsOpen(true);
    }
  };

  return (
    <div className="relative w-full" ref={containerRef}>
      {/* Trigger Button */}
      <button
        type="button"
        role="combobox"
        aria-expanded={isOpen}
        aria-disabled={disabled}
        disabled={disabled}
        onClick={() => !disabled && setIsOpen((prev) => !prev)}
        onKeyDown={handleKeyDown}
        className={`flex w-full items-center justify-between rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground shadow-xs transition-colors hover:border-foreground/40 focus:outline-none focus:ring-1 focus:ring-ring disabled:cursor-not-allowed disabled:opacity-50 h-10 ${className}`}
      >
        <span className="truncate text-left">
          {selectedOption ? selectedOption.label : <span className="text-muted-foreground">{placeholder}</span>}
        </span>
        <ChevronDown
          className={`h-4 w-4 shrink-0 text-muted-foreground transition-transform duration-200 ml-2 ${
            isOpen ? "rotate-180" : ""
          }`}
        />
      </button>

      {/* Floating Dropdown Menu */}
      {isOpen && (
        <div className="absolute left-0 top-full z-50 mt-1.5 w-full min-w-[240px] rounded-lg border border-border bg-popover text-popover-foreground shadow-xl overflow-hidden py-1 max-h-64 overflow-y-auto animate-in fade-in-0 zoom-in-95">
          {normalizedOptions.length === 0 ? (
            <div className="px-3 py-2 text-xs text-muted-foreground text-center">
              No options available
            </div>
          ) : (
            normalizedOptions.map((opt) => {
              const isSelected = opt.value === value;
              return (
                <button
                  key={opt.value}
                  type="button"
                  role="option"
                  aria-selected={isSelected}
                  onClick={() => {
                    onChange(opt.value);
                    setIsOpen(false);
                  }}
                  className={`flex w-full items-center justify-between px-3 py-2 text-left text-sm transition-colors cursor-pointer ${
                    isSelected
                      ? "bg-muted font-semibold text-foreground"
                      : "text-foreground hover:bg-muted/70"
                  }`}
                >
                  <div className="flex flex-col truncate pr-2">
                    <span className="truncate">{opt.label}</span>
                    {opt.sublabel && (
                      <span className="text-xs text-muted-foreground">{opt.sublabel}</span>
                    )}
                  </div>
                  {isSelected && (
                    <Check className="h-4 w-4 shrink-0 text-foreground ml-2" />
                  )}
                </button>
              );
            })
          )}
        </div>
      )}
    </div>
  );
}

