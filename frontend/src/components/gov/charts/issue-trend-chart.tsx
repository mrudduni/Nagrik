"use client"

import { Area, AreaChart, CartesianGrid, XAxis } from "recharts"
import { ChartContainer, ChartTooltip, ChartTooltipContent, type ChartConfig } from "@/components/ui/chart"
import type { TrendPoint } from "@/types"

const chartConfig = {
  value: { label: "Complaints", color: "var(--chart-1)" },
} satisfies ChartConfig

export function IssueTrendChart({ data }: { data: TrendPoint[] }) {
  return (
    <ChartContainer config={chartConfig} className="aspect-auto h-64 w-full">
      <AreaChart data={data} margin={{ left: 0, right: 8, top: 8 }}>
        <defs>
          <linearGradient id="fillValue" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="var(--color-value)" stopOpacity={0.35} />
            <stop offset="95%" stopColor="var(--color-value)" stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <CartesianGrid vertical={false} strokeDasharray="3 3" />
        <XAxis dataKey="date" tickLine={false} axisLine={false} tickMargin={8} interval={4} fontSize={11} />
        <ChartTooltip content={<ChartTooltipContent indicator="dot" />} />
        <Area dataKey="value" type="monotone" fill="url(#fillValue)" stroke="var(--color-value)" strokeWidth={2} />
      </AreaChart>
    </ChartContainer>
  )
}
