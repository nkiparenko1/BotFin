"use client";

import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { apiFetch } from "@/lib/api-client";

const REGIONS = ["Москва", "Санкт-Петербург", "Московская область", "Другой регион"];

export default function OnboardingPage() {
  const { data: session } = useSession();
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [form, setForm] = useState<Record<string, unknown>>({});
  const [plan, setPlan] = useState<string[]>([]);
  const [healthScore, setHealthScore] = useState(0);
  const [loading, setLoading] = useState(false);

  function update(field: string, value: unknown) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function submitStep(nextStep: number) {
    if (!session?.accessToken) return;
    setLoading(true);
    try {
      const res = await apiFetch<{ profile: unknown; health_score: number; plan?: string[] }>(
        "/api/profile/onboarding",
        {
          method: "POST",
          token: session.accessToken,
          body: JSON.stringify({ step: nextStep, data: form }),
        },
      );
      setHealthScore(res.health_score);
      if (res.plan) {
        setPlan(res.plan);
        setStep(4);
      } else {
        setStep(nextStep);
      }
    } finally {
      setLoading(false);
    }
  }

  if (step === 4) {
    return (
      <div className="max-w-lg mx-auto py-12 text-center">
        <h1 className="text-2xl font-bold mb-4">Ваш Financial Health Score</h1>
        <p className="text-5xl font-bold text-primary mb-6">{healthScore}</p>
        <h2 className="font-semibold mb-4">План на 3 шага:</h2>
        <ol className="text-left space-y-3 mb-8">
          {plan.map((s, i) => (
            <li key={i} className="bg-white p-4 rounded-lg border">
              {i + 1}. {s}
            </li>
          ))}
        </ol>
        <button
          onClick={() => router.push("/chat")}
          className="bg-primary text-white px-6 py-3 rounded-lg"
        >
          Перейти в чат
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-lg mx-auto py-12">
      <div className="mb-8">
        <div className="flex gap-2 mb-2">
          {[1, 2, 3].map((s) => (
            <div key={s} className={`h-2 flex-1 rounded ${s <= step ? "bg-primary" : "bg-slate-200"}`} />
          ))}
        </div>
        <p className="text-sm text-slate-500">Шаг {step} из 3</p>
      </div>

      {step === 1 && (
        <div className="space-y-4 bg-white p-6 rounded-xl border">
          <h1 className="text-xl font-bold">Базовая информация</h1>
          <input placeholder="Имя" className="w-full border rounded-lg px-4 py-2" onChange={(e) => update("name", e.target.value)} />
          <input type="number" placeholder="Возраст" className="w-full border rounded-lg px-4 py-2" onChange={(e) => update("age", +e.target.value)} />
          <select className="w-full border rounded-lg px-4 py-2" onChange={(e) => update("family_status", e.target.value)}>
            <option value="">Семейное положение</option>
            <option value="single">Один/одна</option>
            <option value="couple">В паре</option>
            <option value="with_children">С детьми</option>
          </select>
          <select className="w-full border rounded-lg px-4 py-2" onChange={(e) => update("region", e.target.value)}>
            <option value="">Регион</option>
            {REGIONS.map((r) => (
              <option key={r} value={r}>{r}</option>
            ))}
          </select>
          <button onClick={() => submitStep(1)} disabled={loading} className="w-full bg-primary text-white py-2 rounded-lg">
            Далее
          </button>
        </div>
      )}

      {step === 2 && (
        <div className="space-y-4 bg-white p-6 rounded-xl border">
          <h1 className="text-xl font-bold">Финансы</h1>
          <input type="number" placeholder="Доход после налогов, ₽/мес" className="w-full border rounded-lg px-4 py-2" onChange={(e) => update("monthly_income", +e.target.value)} />
          <input type="number" placeholder="Обязательные расходы (ипотека, кредиты)" className="w-full border rounded-lg px-4 py-2" onChange={(e) => update("fixed_expenses", +e.target.value)} />
          <input type="number" placeholder="Переменные расходы (еда, транспорт)" className="w-full border rounded-lg px-4 py-2" onChange={(e) => update("variable_expenses", +e.target.value)} />
          <input type="number" placeholder="Накопления (опционально)" className="w-full border rounded-lg px-4 py-2" onChange={(e) => update("savings", +e.target.value)} />
          <label className="flex items-center gap-2">
            <input type="checkbox" onChange={(e) => update("has_loans", e.target.checked)} />
            Есть кредиты/ипотека
          </label>
          <input type="number" placeholder="Сумма платежей по кредитам" className="w-full border rounded-lg px-4 py-2" onChange={(e) => update("loan_payment", +e.target.value)} />
          <button onClick={() => submitStep(2)} disabled={loading} className="w-full bg-primary text-white py-2 rounded-lg">
            Далее
          </button>
        </div>
      )}

      {step === 3 && (
        <div className="space-y-4 bg-white p-6 rounded-xl border">
          <h1 className="text-xl font-bold">Цели и опыт</h1>
          <select className="w-full border rounded-lg px-4 py-2" onChange={(e) => update("main_goal", e.target.value)}>
            <option value="">Основная цель</option>
            <option value="emergency">Подушка безопасности</option>
            <option value="apartment">Квартира</option>
            <option value="pension">Пенсия</option>
            <option value="education">Образование</option>
          </select>
          <input type="number" placeholder="Срок цели (лет)" className="w-full border rounded-lg px-4 py-2" onChange={(e) => update("goal_years", +e.target.value)} />
          <select className="w-full border rounded-lg px-4 py-2" onChange={(e) => update("investment_exp", e.target.value)}>
            <option value="none">Опыт инвестиций: нет</option>
            <option value="read">Читал о инвестициях</option>
            <option value="trading">Торгую</option>
          </select>
          <select className="w-full border rounded-lg px-4 py-2" onChange={(e) => update("risk_level", e.target.value)}>
            <option value="conservative">Консервативный</option>
            <option value="moderate">Умеренный</option>
            <option value="aggressive">Агрессивный</option>
          </select>
          <button onClick={() => submitStep(3)} disabled={loading} className="w-full bg-primary text-white py-2 rounded-lg">
            Завершить
          </button>
        </div>
      )}
    </div>
  );
}
