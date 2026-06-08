"use client";

import { useSession } from "next-auth/react";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { apiFetch } from "@/lib/api-client";

export default function GoalDetailPage({ params }: { params: { id: string } }) {
  const { data: session } = useSession();
  const [data, setData] = useState<{
    goal: Record<string, unknown>;
    calculations: { monthly_deposit: number; progress_pct: number; scenarios: Record<string, number> };
  } | null>(null);

  useEffect(() => {
    if (!session?.accessToken) return;
    apiFetch<{
      goal: Record<string, unknown>;
      calculations: { monthly_deposit: number; progress_pct: number; scenarios: Record<string, number> };
    }>(`/api/goals/${params.id}`, { token: session.accessToken }).then(setData);
  }, [session, params.id]);

  if (!data) return <AppShell><p>Загрузка...</p></AppShell>;

  const { goal, calculations } = data;
  const scenarios = calculations.scenarios;

  return (
    <AppShell>
      <h1 className="text-2xl font-bold mb-4">{goal.name as string}</h1>
      <div className="bg-white p-6 rounded-xl border space-y-4 max-w-lg">
        <p>Цель: {Number(goal.target_amount).toLocaleString("ru-RU")} ₽</p>
        <p>Накоплено: {Number(goal.current_amount).toLocaleString("ru-RU")} ₽</p>
        <p>Ежемесячный взнос: {calculations.monthly_deposit.toLocaleString("ru-RU")} ₽</p>
        <div className="w-full bg-slate-100 rounded-full h-3">
          <div className="bg-primary h-3 rounded-full" style={{ width: `${calculations.progress_pct}%` }} />
        </div>
        <h2 className="font-semibold pt-4">Сценарии</h2>
        <p className="text-sm">+10% к взносу: {scenarios.deposit_plus_10_pct?.toLocaleString("ru-RU")} ₽/мес</p>
        <p className="text-sm">+1 год к сроку: {scenarios.deposit_with_extra_year?.toLocaleString("ru-RU")} ₽/мес</p>
      </div>
    </AppShell>
  );
}
