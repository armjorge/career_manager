import { useMemo } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { Alert } from '@/components/ui/Alert'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { useAnalyticsSummary } from '@/hooks/useAnalytics'
import type { AnalyticsSummary } from '@/types'

const CHART_COLORS = ['#3b82f6', '#22c55e', '#f59e0b', '#a855f7', '#ef4444', '#06b6d4', '#ec4899']

const tooltipStyle = {
  backgroundColor: '#1a2332',
  border: '1px solid #2d3a4f',
  borderRadius: '8px',
  color: '#e8edf4',
}

function MetricCard({ label, value }: { label: string; value: string | number }) {
  return (
    <Card>
      <p className="text-sm text-muted">{label}</p>
      <p className="mt-2 text-3xl font-semibold tracking-tight text-foreground">{value}</p>
    </Card>
  )
}

function EmptyChart({ message }: { message: string }) {
  return (
    <div className="flex h-64 items-center justify-center rounded-lg border border-dashed border-border bg-surface-elevated/30 px-6 text-center text-sm text-muted">
      {message}
    </div>
  )
}

function buildInsights(data: AnalyticsSummary) {
  const insights: string[] = []
  const { metrics, monthlyActivity, industryDistribution, categoryDistribution } = data

  if (monthlyActivity.length > 0) {
    const peak = [...monthlyActivity].sort((a, b) => b.apps - a.apps)[0]
    insights.push(
      `Peak momentum: your highest output was in ${peak.yearMonth}. Can you beat that this month?`,
    )
  }

  if (industryDistribution.length > 0) {
    insights.push(
      `Primary industry: you are focusing heavily on ${industryDistribution[0].name}.`,
    )
  }

  if (metrics.cvPrepRate < 70) {
    insights.push(
      `Workflow tip: document readiness is at ${metrics.cvPrepRate.toFixed(1)}%. Generate your CV right after creating an application.`,
    )
  } else if (metrics.totalApplications > 0) {
    insights.push('High efficiency: you have a ready CV for most applications. Stay agile for recruiter calls.')
  }

  if (categoryDistribution.length > 0) {
    insights.push(
      `Top role: most applications target ${categoryDistribution[0].name} positions.`,
    )
  }

  return insights
}

export function AnalyticsPage() {
  const { data, isLoading, isError, error } = useAnalyticsSummary()

  const insights = useMemo(() => (data ? buildInsights(data) : []), [data])

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Analytics</h1>
          <p className="mt-2 text-muted">Loading pipeline metrics…</p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {Array.from({ length: 4 }).map((_, index) => (
            <Card key={index} className="h-24 animate-pulse bg-surface-elevated/40" />
          ))}
        </div>
      </div>
    )
  }

  if (isError || !data) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Analytics</h1>
        </div>
        <Alert
          variant="error"
          message={error instanceof Error ? error.message : 'Could not load analytics.'}
        />
      </div>
    )
  }

  const { metrics, monthlyActivity, statusDistribution, languageDistribution, categoryDistribution, industryDistribution } =
    data

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Application Analytics & Insights</h1>
        <p className="mt-2 max-w-3xl text-muted">
          Pipeline metrics, monthly trends, and market focus — based on your applications and document
          readiness.
        </p>
      </div>

      <section className="space-y-4">
        <h2 className="text-xl font-semibold">Overall progress</h2>
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <MetricCard label="Total applications" value={metrics.totalApplications} />
          <MetricCard label="Ready resumes" value={metrics.readyResumes} />
          <MetricCard label="Ready cover letters" value={metrics.readyCoverLetters} />
          <MetricCard label="CV prep rate" value={`${metrics.cvPrepRate.toFixed(1)}%`} />
        </div>
      </section>

      <section className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle>Monthly activity</CardTitle>
            <CardDescription>Applications vs. document readiness over time</CardDescription>
          </CardHeader>
          {monthlyActivity.length > 0 ? (
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={monthlyActivity}>
                  <CartesianGrid stroke="#2d3a4f" strokeDasharray="3 3" />
                  <XAxis dataKey="yearMonth" stroke="#8b9cb3" tick={{ fill: '#8b9cb3', fontSize: 12 }} />
                  <YAxis stroke="#8b9cb3" tick={{ fill: '#8b9cb3', fontSize: 12 }} allowDecimals={false} />
                  <Tooltip contentStyle={tooltipStyle} />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="apps"
                    name="Applications"
                    stroke={CHART_COLORS[0]}
                    strokeWidth={2}
                    dot={{ r: 4 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="resumes"
                    name="Ready resumes"
                    stroke={CHART_COLORS[1]}
                    strokeWidth={2}
                    dot={{ r: 4 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="coverLetters"
                    name="Ready cover letters"
                    stroke={CHART_COLORS[2]}
                    strokeWidth={2}
                    dot={{ r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <EmptyChart message="No data yet. Create applications to see monthly trends." />
          )}
        </Card>
      </section>

      <section className="space-y-4">
        <h2 className="text-xl font-semibold">Market focus</h2>
        <div className="grid gap-4 xl:grid-cols-3">
          <Card>
            <CardHeader>
              <CardTitle>Job categories</CardTitle>
            </CardHeader>
            {categoryDistribution.length > 0 ? (
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={categoryDistribution}
                      dataKey="count"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      innerRadius={55}
                      outerRadius={90}
                      paddingAngle={2}
                    >
                      {categoryDistribution.map((entry, index) => (
                        <Cell key={entry.name} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={tooltipStyle} />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <EmptyChart message="No categories yet." />
            )}
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Industries / company types</CardTitle>
            </CardHeader>
            {industryDistribution.length > 0 ? (
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={industryDistribution} layout="vertical" margin={{ left: 12, right: 12 }}>
                    <CartesianGrid stroke="#2d3a4f" strokeDasharray="3 3" horizontal={false} />
                    <XAxis type="number" stroke="#8b9cb3" tick={{ fill: '#8b9cb3', fontSize: 12 }} allowDecimals={false} />
                    <YAxis
                      type="category"
                      dataKey="name"
                      width={110}
                      stroke="#8b9cb3"
                      tick={{ fill: '#8b9cb3', fontSize: 11 }}
                    />
                    <Tooltip contentStyle={tooltipStyle} />
                    <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                      {industryDistribution.map((entry, index) => (
                        <Cell key={entry.name} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <EmptyChart message="No industry data yet." />
            )}
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Languages</CardTitle>
            </CardHeader>
            {languageDistribution.length > 0 ? (
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={languageDistribution}
                      dataKey="count"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      innerRadius={55}
                      outerRadius={90}
                      paddingAngle={2}
                    >
                      {languageDistribution.map((entry, index) => (
                        <Cell key={entry.name} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={tooltipStyle} />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <EmptyChart message="No language data yet." />
            )}
          </Card>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-xl font-semibold">Current status</h2>
        <div className="grid gap-4 lg:grid-cols-[2fr_1fr]">
          <Card>
            {statusDistribution.length > 0 ? (
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={statusDistribution}>
                    <CartesianGrid stroke="#2d3a4f" strokeDasharray="3 3" />
                    <XAxis dataKey="name" stroke="#8b9cb3" tick={{ fill: '#8b9cb3', fontSize: 12 }} />
                    <YAxis stroke="#8b9cb3" tick={{ fill: '#8b9cb3', fontSize: 12 }} allowDecimals={false} />
                    <Tooltip contentStyle={tooltipStyle} />
                    <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                      {statusDistribution.map((entry, index) => (
                        <Cell key={entry.name} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <EmptyChart message="No applications yet." />
            )}
          </Card>

          <Card className="flex items-center">
            <Alert
              variant="info"
              message="Keep it up! Consistency is key in the job hunt. Every application is a step closer — don't forget to follow up on open applications."
            />
          </Card>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-xl font-semibold">Strategic insights</h2>
        <Card>
          {insights.length > 0 ? (
            <ul className="space-y-3 text-sm text-foreground">
              {insights.map((insight) => (
                <li key={insight} className="flex gap-2">
                  <span className="text-primary">•</span>
                  <span>{insight}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted">
              Add applications to unlock personalized insights about your search strategy.
            </p>
          )}
          <p className="mt-5 border-t border-border pt-4 text-sm text-muted">
            Job hunting is a marathon, not a sprint. Use these analytics to refine your strategy and
            keep moving forward.
          </p>
        </Card>
      </section>
    </div>
  )
}
