"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { signOut, useSession } from "next-auth/react";
import clsx from "clsx";

const NAV = [
  { href: "/dashboard", label: "Главная" },
  { href: "/chat", label: "Чат" },
  { href: "/budget", label: "Бюджет" },
  { href: "/goals", label: "Цели" },
  { href: "/tax", label: "Налоги" },
  { href: "/profile", label: "Профиль" },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { data: session } = useSession();

  return (
    <div className="min-h-screen flex">
      <aside className="w-56 bg-white border-r border-[var(--border)] p-4 hidden md:block">
        <Link href="/dashboard" className="font-bold text-lg text-primary block mb-8">
          BotFin
        </Link>
        <nav className="space-y-1">
          {NAV.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={clsx(
                "block px-3 py-2 rounded-lg text-sm",
                pathname.startsWith(item.href)
                  ? "bg-primary text-white"
                  : "text-slate-600 hover:bg-slate-100",
              )}
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <button
          onClick={() => signOut({ callbackUrl: "/" })}
          className="mt-8 text-sm text-slate-500 hover:text-slate-800"
        >
          Выйти ({session?.user?.name})
        </button>
      </aside>
      <main className="flex-1 p-4 md:p-8">{children}</main>
    </div>
  );
}
