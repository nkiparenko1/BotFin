"use client";

import Link from "next/link";
import { useSession } from "next-auth/react";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { HealthScoreCard } from "@/components/HealthScoreCard";
import { apiFetch } from "@/lib/api-client";
import { useRouter } from "next/navigation";

export default function DashboardPage() {
  const { data: session } = useSession();
  const router = useRouter();
  const [score, setScore] = useState(0);
  const [name, setName] = useState("");

  useEffect(() => {
    if (!session?.accessToken) return;
    apiFetch<{ profile: { health_score?: number; onboarding_done?: boolean; name?: string }; health_score?: number }>(
      "/api/profile",
      { token: session.accessToken },
    ).then((res) => {
      if (res.profile && !res.profile.onboarding_done) {
        router.push("/onboarding");
        return;
      }
      setScore(res.health_score || res.profile?.health_score || 0);
    });
    apiFetch<{ user: { name?: string } }>("/api/auth/me", { token: session.accessToken }).then((res) => {
      setName(res.user.name || "");
    });
  }, [session, router]);

  return (
    <AppShell>
      <h1 className="text-2xl font-bold mb-2">Привет, {name}!</h1>
      <p className="text-slate-600 mb-8">Ваш финансовый обзор</p>

      <div className="grid md:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-xl border flex justify-center">
          <HealthScoreCard score={score} />
        </div>
        <div className="bg-white p-6 rounded-xl border">
          <h2 className="font-semibold mb-4">Быстрые действия</h2>
          <div className="space-y-2">
            <Link href="/chat" className="block p-3 rounded-lg bg-slate-50 hover:bg-slate-100">
              Спросить AI-советника
            </Link>
            <Link href="/budget" className="block p-3 rounded-lg bg-slate-50 hover:bg-slate-100">
              Добавить расход
            </Link>
            <Link href="/tax" className="block p-3 rounded-lg bg-slate-50 hover:bg-slate-100">
              Проверить налоговые вычеты
            </Link>
            <Link href="/goals" className="block p-3 rounded-lg bg-slate-50 hover:bg-slate-100">
              Создать финансовую цель
            </Link>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
