import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Toaster } from "@/components/ui/sonner";
import { AppProvider } from "@/context/app-provider";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "NAGRIK - Smart Civic Platform",
  description: "Your AI-powered digital citizen companion for government schemes and civic services.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
      suppressHydrationWarning
    >
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              try {
                const removeBadAttrs = function(el) {
                  if (!el || !el.attributes) return;
                  for (let i = el.attributes.length - 1; i >= 0; i--) {
                    const attr = el.attributes[i].name;
                    if (attr.indexOf('bis_') === 0 || attr.indexOf('__processed_') === 0) {
                      el.removeAttribute(attr);
                    }
                  }
                };
                const observer = new MutationObserver(function(mutations) {
                  for (let i = 0; i < mutations.length; i++) {
                    const m = mutations[i];
                    if (m.type === 'attributes' && m.target) {
                      removeBadAttrs(m.target);
                    } else if (m.type === 'childList') {
                      for (let j = 0; j < m.addedNodes.length; j++) {
                        const node = m.addedNodes[j];
                        if (node.nodeType === 1) {
                          removeBadAttrs(node);
                          if (node.querySelectorAll) {
                            const children = node.querySelectorAll('*');
                            for (let k = 0; k < children.length; k++) {
                              removeBadAttrs(children[k]);
                            }
                          }
                        }
                      }
                    }
                  }
                });
                observer.observe(document.documentElement, {
                  attributes: true,
                  childList: true,
                  subtree: true
                });
                if (document.querySelectorAll) {
                  const all = document.querySelectorAll('*');
                  for (let i = 0; i < all.length; i++) {
                    removeBadAttrs(all[i]);
                  }
                }
              } catch (e) {}
            `,
          }}
        />
      </head>
      <body
        className="min-h-full flex flex-col bg-background text-foreground"
        suppressHydrationWarning
      >
        <AppProvider>
          <TooltipProvider delayDuration={200}>
            {children}
            <Toaster position="top-right" richColors closeButton />
          </TooltipProvider>
        </AppProvider>
      </body>
    </html>
  );
}
