"use client";

import Link from "next/link";
import { useSession } from "next-auth/react";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { apiFetch } from "@/lib/api-client";

interface GoalItem {
  goal: {
    id: string;
    name: string;
    target_amount: number;
    current_amount: number;
    monthly_deposit: number;
    deadline_months: number;
    status: string;
  };
  calculations: {
    monthly_deposit: number;
    progress_pct: number;
    scenarios: Record<string, number>;
  };
}

export default function GoalsPage() {
  const { data: session } = useSession();
  const [goals, setGoals] = useState<GoalItem[]>([]);
  const [name, setName] = useState("");
  const [target, setTarget] = useState("");
  const [months, setMonths] = useState("12");
  const [error, setError] = useState("");

  function load() {
    if (!session?.accessToken) return;
    apiFetch<GoalItem[]>("/api/goals", { token: session.accessToken }).then(setGoals);
  }

  useEffect(load, [session]);

  async function createGoal(e: React.FormEvent) {
    e.preventDefault();
    if (!session?.accessToken) return;
    setError("");
    try {
      await apiFetch("/api/goals", {
        method: "POST",
        token: session.accessToken,
        body: JSON.stringify({
          name,
          target_amount: +target,
          deadline_months: +months,
        }),
      });
      setName("");
      setTarget("");
      load();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <AppShell>
      <h1 className="text-2xl font-bold mb-6">Финансовые цели</h1>

      <form onSubmit={createGoal} className="bg-white p-6 rounded-xl border mb-6 space-y-3 max-w-md">
        <h2 className="font-semibold">Новая цель (лимит Free: 1)</h2>
        <input placeholder="Название" value={name} onChange={(e) => setName(e.target.value)} className="w-full border rounded-lg px-3 py-2" required />
        <input type="number" placeholder="Целевая сумма, ₽" value={target} onChange={(e) => setTarget(e.target.value)} className="w-full border rounded-lg px-3 py-2" required />
        <input type="number" placeholder="Срок, месяцев" value={months} onChange={(e) => setMonths(e.target.value)} className="w-full border rounded-lg px-3 py-2" required />
        {error && <p className="text-red-500 text-sm">{error}</p>}
        <button type="submit" className="w-full bg-primary text-white py-2 rounded-lg">Создать</button>
      </form>

      <div className="space-y-4">
        {goals.map(({ goal, calculations }) => (
          <Link key={goal.id} href={`/goals/${goal.id}`} className="block bg-white p-6 rounded-xl border hover:border-primary">
            <div className="flex justify-between mb-2">
              <h3 className="font-semibold">{goal.name}</h3>
              <span className="text-sm text-slate-500">{calculations.progress_pct.toFixed(0)}%</span>
            </div>
            <div className="w-full bg-slate-100 rounded-full h-2 mb-2">
              <div className="bg-primary h-2 rounded-full" style={{ width: `${calculations.progress_pct}%` }} />
            </div>
            <p className="text-sm text-slate-600">
              Взнос: {calculations.monthly_deposit.toLocaleString("ru-RU")} ₽/мес · Цель: {Number(goal.target_amount).toLocaleString("ru-RU")} ₽
            </p>
          </Link>
        ))}
      </div>
    </AppShell>
  );
}
