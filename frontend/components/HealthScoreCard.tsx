"use client";

interface HealthScoreCardProps {
  score: number;
  size?: "sm" | "lg";
}

export function HealthScoreCard({ score, size = "lg" }: HealthScoreCardProps) {
  const color = score >= 70 ? "#22c55e" : score >= 40 ? "#eab308" : "#ef4444";
  const dim = size === "lg" ? 120 : 80;
  const radius = 45;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  return (
    <div className="flex flex-col items-center">
      <svg width={dim} height={dim} viewBox="0 0 100 100">
        <circle cx="50" cy="50" r={radius} fill="none" stroke="#e2e8f0" strokeWidth="8" />
        <circle
          cx="50"
          cy="50"
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform="rotate(-90 50 50)"
        />
        <text x="50" y="50" textAnchor="middle" dy="0.35em" className="text-xl font-bold fill-slate-800">
          {score}
        </text>
      </svg>
      <p className="text-sm text-slate-500 mt-2">Financial Health Score</p>
    </div>
  );
}
