import "./globals.css";
import { TooltipProvider } from "@/components/ui/tooltip";

export const metadata = {
  title: "PromoMind AI — Retail Intelligence & Demand OS",
  description: "AI-Powered Demand Forecasting, Dynamic Sales Copilot & Capital Profit Optimization for Retail & Commerce",
  icons: {
    icon: [
      { url: "/icon.svg", type: "image/svg+xml" },
    ],
    shortcut: "/icon.svg",
    apple: "/icon.svg",
  },
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className="h-full antialiased light">
      <body className="min-h-full flex flex-col bg-background text-foreground font-sans selection:bg-primary/10 selection:text-primary">
        <TooltipProvider>{children}</TooltipProvider>
      </body>
    </html>
  );
}
