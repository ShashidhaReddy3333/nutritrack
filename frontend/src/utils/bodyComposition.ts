import type { BodyCompositionReport } from '../types'

type MetricDef = { key: string; label: string }

const SUMMARY_FIELDS: MetricDef[] = [
  { key: 'total_body_weight', label: 'Total Body Weight' },
  { key: 'lean_body_mass', label: 'Lean Body Mass' },
  { key: 'total_body_water', label: 'Total Body Water' },
  { key: 'skeletal_muscle_mass', label: 'Skeletal Muscle Mass' },
  { key: 'total_fat_mass', label: 'Total Fat Mass' },
]

const BODY_COMPOSITION_FIELDS: MetricDef[] = [
  { key: 'protein', label: 'Protein' },
  { key: 'mineral', label: 'Mineral' },
  { key: 'visceral_fat_area', label: 'Visceral Fat Area' },
  { key: 'total_body_fat_percentage', label: 'Total Body Fat Percentage' },
  { key: 'visceral_fat_level', label: 'Visceral Fat Level' },
  { key: 'intracellular_fluid', label: 'Intracellular Fluid (ICF)' },
  { key: 'extracellular_fluid', label: 'Extracellular Fluid (ECF)' },
  { key: 'basal_metabolic_rate', label: 'Basal Metabolic Rate (BMR)' },
  { key: 'total_energy_expenditure', label: 'Total Energy Expenditure (TEE)' },
  { key: 'subcutaneous_fat_mass', label: 'Subcutaneous Fat Mass' },
  { key: 'visceral_fat_mass', label: 'Visceral Fat Mass' },
]

const SEGMENTAL_FIELDS: MetricDef[] = [
  { key: 'left_arm_lean_mass', label: 'Left Arm Lean Mass' },
  { key: 'right_arm_lean_mass', label: 'Right Arm Lean Mass' },
  { key: 'left_leg_lean_mass', label: 'Left Leg Lean Mass' },
  { key: 'right_leg_lean_mass', label: 'Right Leg Lean Mass' },
  { key: 'torso_lean_mass', label: 'Torso Lean Mass' },
  { key: 'left_arm_fat_mass', label: 'Left Arm Fat Mass' },
  { key: 'right_arm_fat_mass', label: 'Right Arm Fat Mass' },
  { key: 'left_leg_fat_mass', label: 'Left Leg Fat Mass' },
  { key: 'right_leg_fat_mass', label: 'Right Leg Fat Mass' },
  { key: 'torso_fat_mass', label: 'Torso Fat Mass' },
]

const TOP_LEVEL_FIELDS: MetricDef[] = [
  { key: 'bwi_result', label: 'BWI RESULT' },
  { key: 'bio_age', label: 'Bio Age' },
  { key: 'waist_to_hip_ratio', label: 'Waist to Hip Ratio' },
]

const SECTION_HEADERS = new Set(['SUMMARY', 'BODY COMPOSITION', 'SEGMENTAL ANALYSIS'])
const ALL_FIELDS = [...TOP_LEVEL_FIELDS, ...SUMMARY_FIELDS, ...BODY_COMPOSITION_FIELDS, ...SEGMENTAL_FIELDS]

function emptyReport(): BodyCompositionReport {
  return {
    summary: {},
    body_composition: {},
    segmental_analysis: {},
  }
}

function assignMetric(report: BodyCompositionReport, label: string, value: string) {
  const topLevel = TOP_LEVEL_FIELDS.find((field) => field.label === label)
  if (topLevel) {
    if (topLevel.key === 'bwi_result') report.bwi_result = value
    if (topLevel.key === 'bio_age') report.bio_age = value
    if (topLevel.key === 'waist_to_hip_ratio') report.waist_to_hip_ratio = value
    return
  }

  const summary = SUMMARY_FIELDS.find((field) => field.label === label)
  if (summary) {
    report.summary[summary.key] = value
    return
  }

  const body = BODY_COMPOSITION_FIELDS.find((field) => field.label === label)
  if (body) {
    report.body_composition[body.key] = value
    return
  }

  const segment = SEGMENTAL_FIELDS.find((field) => field.label === label)
  if (segment) {
    report.segmental_analysis[segment.key] = value
  }
}

function findInlineMetric(line: string): { label: string; value: string } | null {
  for (const field of ALL_FIELDS) {
    if (line === field.label) {
      return null
    }
    if (line.startsWith(`${field.label} `)) {
      const value = line.slice(field.label.length).trim()
      if (value) return { label: field.label, value }
    }
  }
  return null
}

export function parseBodyCompositionReport(rawText: string): BodyCompositionReport | null {
  const lines = rawText
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)

  const report = emptyReport()
  let pendingLabel: string | null = null
  let foundCount = 0

  for (const line of lines) {
    if (SECTION_HEADERS.has(line)) {
      pendingLabel = null
      continue
    }

    if (pendingLabel) {
      assignMetric(report, pendingLabel, line)
      pendingLabel = null
      foundCount += 1
      continue
    }

    const inlineMetric = findInlineMetric(line)
    if (inlineMetric) {
      assignMetric(report, inlineMetric.label, inlineMetric.value)
      foundCount += 1
      continue
    }

    const exactMetric = ALL_FIELDS.find((field) => field.label === line)
    if (exactMetric) {
      pendingLabel = exactMetric.label
    }
  }

  return foundCount > 0 ? report : null
}

export { BODY_COMPOSITION_FIELDS, SEGMENTAL_FIELDS, SUMMARY_FIELDS, TOP_LEVEL_FIELDS }
