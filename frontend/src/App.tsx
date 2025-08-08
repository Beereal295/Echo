import { Routes, Route } from 'react-router-dom'
import { Toaster } from '@/components/ui/toaster'
import Layout from '@/components/layout/Layout'
import HomePage from '@/pages/HomePage'
import NewEntryPage from '@/pages/NewEntryPage'
import VoiceUploadPage from '@/pages/VoiceUploadPage'
import ViewEntriesPage from '@/pages/ViewEntriesPage'
import TalkToYourDiaryPage from '@/pages/TalkToYourDiaryPage'
import PatternInsightsPage from '@/pages/PatternInsightsPage'
import MemoriesPage from '@/pages/MemoriesPage'
import SettingsPage from '@/pages/SettingsPage'

function App() {
  return (
    <div className="min-h-screen bg-background font-sans antialiased">
      <Layout>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/new" element={<NewEntryPage />} />
          <Route path="/voice-upload" element={<VoiceUploadPage />} />
          <Route path="/entries" element={<ViewEntriesPage />} />
          <Route path="/talk" element={<TalkToYourDiaryPage />} />
          <Route path="/patterns" element={<PatternInsightsPage />} />
          <Route path="/memories" element={<MemoriesPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </Layout>
      <Toaster />
    </div>
  )
}

export default App