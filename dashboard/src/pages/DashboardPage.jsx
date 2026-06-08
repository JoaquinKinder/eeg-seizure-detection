import { useState, useEffect } from 'react'
import Header from '../components/Header'
import MetaBar from '../components/MetaBar'
import KpiGrid from '../components/KpiGrid'
import SensibilityChart from '../components/SensibilityChart'
import AucFaCharts from '../components/AucFaCharts'
import TimelineGallery from '../components/TimelineGallery'
import RadarComparativo from '../components/RadarComparativo'
import MetricsTable from '../components/MetricsTable'
import PatientGrid from '../components/PatientGrid'
import Footer from '../components/Footer'
import Loader from '../components/Loader'

import styles from '../App.module.css'

export default function DashboardPage() {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch('/results.json')
      .then(res => {
        if (!res.ok) throw new Error('No se pudo cargar results.json')
        return res.json()
      })
      .then(json => setData(json))
      .catch(err => setError(err.message))
  }, [])

  if (error) return <div className={styles.error}>Error: {error}</div>
  if (!data) return <Loader />

  return (
    <div className={styles.app}>
      <Header />
      <MetaBar meta={data.metadata} />
      <KpiGrid data={data} />
      <SensibilityChart data={data} />
      <AucFaCharts data={data} />
      <TimelineGallery patients={data.metadata.patients} />
      <RadarComparativo data={data} />
      <MetricsTable data={data} />
      <PatientGrid data={data} />
      <Footer />
    </div>
  )
}
