import { cn as baseCn } from "cn";

export function cn(...inputs) {
  if (typeof baseCn === "function") {
    return baseCn(...inputs);
  }
  return inputs.flat(Infinity).filter(Boolean).join(" ");
}
