import "@aws-amplify/ui-react/styles.css";
import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "Faceflow",
  description: "Cloud-first face grouping & sharing demo"
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-950 text-slate-100">
        <main className="mx-auto flex max-w-5xl flex-col gap-6 px-6 py-10">
          {children}
        </main>
      </body>
    </html>
  );
}
