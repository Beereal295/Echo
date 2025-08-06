import { motion, AnimatePresence } from 'framer-motion'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { FileText, Sparkles, Zap, Pen, BookOpen, Clock, FileAudio2 } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { api } from '@/lib/api'
import { format } from 'date-fns'

function HomePage() {
  const navigate = useNavigate()
  const [insights, setInsights] = useState<string[]>([])
  const [currentInsightIndex, setCurrentInsightIndex] = useState(0)
  const [entries, setEntries] = useState<any[]>([])
  const [currentTime, setCurrentTime] = useState(new Date())
  const [currentSnark, setCurrentSnark] = useState('')
  const [displayedSnark, setDisplayedSnark] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [showPlusMenu, setShowPlusMenu] = useState(false)

  // Load user data for insights
  useEffect(() => {
    loadUserData()
  }, [])

  // Time-based snarky comments
  const snarkyComments = {
    0: ["Midnight. Still here. Still overthinking. Still fabulous.", "12 AM: I am both the problem and the insomniac solution.", "It's midnight and I've never felt more creative or useless.", "12 AM: fueled by delusion and glowing screens."],
    1: ["It's 1 AM. Perfect time to replay arguments in my head like a greatest hits album.", "1 AM: where \"just one more episode\" becomes five.", "1 AM and I've suddenly decided to rebrand my whole personality.", "1 AM: brain is loud, world is quiet, regrets are echoing."],
    2: ["2 AM. Overthinking? Check. Hydrated? No.", "2 AM is just diet sadness with worse lighting.", "It's 2 AM. I've solved zero problems and invented three new ones.", "2 AM: the hour my inner monologue turns into a TED Talk no one asked for."],
    3: ["3 AM: Why sleep when I can spiral in style?", "3 AM. Body tired. Brain: what if dinosaurs had anxiety?", "It's 3 AM and my pillow just became a therapy session.", "3 AM: unlocked a new memory to cringe about forever."],
    4: ["4 AM: Birds are chirping. I'm still a disaster.", "It's 4 AM and the only thing up is my cortisol.", "4 AM: technically morning, emotionally a haunted house.", "4 AM: nature wakes up, and so does my self-doubt."],
    5: ["5 AM. Too early to function, too late to pretend I slept.", "5 AM: when you're not awake on purpose, just on accident.", "It's 5 AM and I'm watching the sun rise out of spite.", "5 AM: the sky's changing and so is my grip on sanity."],
    6: ["6 AM: my alarm clock hates me and honestly? Valid.", "6 AM and I'm already 3 years behind on life.", "It's 6 AM. Should I meditate or scream quietly?", "6 AM: the day starts, but I do not."],
    7: ["7 AM. I'm vertical but not thriving.", "7 AM: awake in body, missing in spirit.", "It's 7 AM and I'm already Googling how to fake enthusiasm.", "7 AM: coffee's hot, my ambition is lukewarm."],
    8: ["8 AM. Pretending I'm a productive citizen again.", "It's 8 AM and the email avalanche begins.", "8 AM: fully dressed in despair and denim.", "8 AM: caffeine loading, willpower buffering."],
    9: ["9 AM. I've opened five tabs and zero intentions.", "9 AM: work mode ON, motivation OFF.", "It's 9 AM and I'm already pretending to be in a meeting.", "9 AM: crushing emails like dreams."],
    10: ["10 AM: halfway to lunch, emotionally at the end.", "10 AM and I still haven't accepted that I'm awake.", "It's 10 AM. Time to pretend I understand my job.", "10 AM: thriving, if your definition of thriving is \"not crying yet.\""],
    11: ["11 AM: I'm not procrastinating. I'm time traveling inefficiently.", "It's 11 AM. I've done nothing but feel busy.", "11 AM: floating between coffee and crisis.", "11 AM: is it too early to call it a day?"],
    12: ["12 PM: Lunch? Already? I did so little to deserve this.", "Noon. Halfway to nowhere, fueled by snacks and sarcasm.", "12 PM: the sun is at its peak, unlike me.", "It's 12 PM and I've contributed one (1) sigh to society."],
    13: ["1 PM: productivity's ghost hour.", "1 PM and I'm just a meat puppet staring at a screen.", "It's 1 PM. Still pretending that spreadsheet makes sense.", "1 PM: brain left the chat."],
    14: ["2 PM. Daydreaming about escape plans and snacks.", "It's 2 PM: hunger, confusion, and fake smiling.", "2 PM: I've hit the wall. The wall hit back.", "2 PM: the hour of unproductive rebellion."],
    15: ["3 PM. Caffeine gone. Hope vanished. Just vibes.", "It's 3 PM and I've opened my 19th tab of denial.", "3 PM: The day's still happening and I deeply resent that.", "3 PM: brain melted. Only sarcasm remains."],
    16: ["4 PM. Energy low. Complaints high.", "It's 4 PM. I'm technically conscious but emotionally buffering.", "4 PM: Why is this meeting happening to me?", "4 PM: fading faster than my phone battery."],
    17: ["5 PM. Workday ends, existential crisis begins.", "5 PM: I survived. Somehow. Barely.", "It's 5 PM. I've earned the right to collapse.", "5 PM: logging off but still dead inside."],
    18: ["6 PM: cooking? Or just eating crackers over the sink?", "It's 6 PM. The food is hot, my standards are low.", "6 PM: Dinner plans? You mean depression with a side of pasta?", "6 PM: feasting like a raccoon in emotional recovery."],
    19: ["7 PM. I call this meal: chaos and calories.", "7 PM: too late to be productive, too early to sleep.", "It's 7 PM. Nothing makes sense, but the snacks are here.", "7 PM: vibes are weird, leftovers are divine."],
    20: ["8 PM: intentionally ignoring the dishes.", "8 PM: Peak delusion hour. I'm totally going to clean my life now.", "It's 8 PM. Netflix, take the wheel.", "8 PM: productivity now legally prohibited."],
    21: ["9 PM: where guilt meets popcorn.", "9 PM: I should be sleeping. Instead, I'm reorganizing my trauma.", "It's 9 PM. Let's start a hobby we'll never finish.", "9 PM: the hour of unrealistic intentions."],
    22: ["10 PM. One more episode = three less hours of sleep.", "10 PM: truly a time for poor decisions and blanket forts.", "It's 10 PM and I'm just getting weird now.", "10 PM: peak \"I swear I'll go to bed soon\" energy."],
    23: ["11 PM: I'm awake and dramatic for no reason.", "11 PM: bedtime is a concept, not a reality.", "It's 11 PM. I'm texting people I shouldn't and opening apps I hate.", "11 PM: just one last scroll... for science."]
  }

  // Update time and snarky comment
  useEffect(() => {
    const updateTimeAndSnark = () => {
      const now = new Date()
      setCurrentTime(now)
      const hour = now.getHours()
      const comments = snarkyComments[hour as keyof typeof snarkyComments] || ["Time to reflect with Echo"]
      setCurrentSnark(comments[Math.floor(Math.random() * comments.length)])
    }

    updateTimeAndSnark()
    const interval = setInterval(updateTimeAndSnark, 60000) // Update every minute
    return () => clearInterval(interval)
  }, [])

  // Typewriter effect for snarky comments
  useEffect(() => {
    if (!currentSnark) return

    // Start typing after all other animations are done (delay matches other elements + buffer)
    const startDelay = setTimeout(() => {
      setIsTyping(true)
      setDisplayedSnark('')
      
      let index = 0
      const typeInterval = setInterval(() => {
        if (index < currentSnark.length) {
          setDisplayedSnark(currentSnark.slice(0, index + 1))
          index++
        } else {
          setIsTyping(false)
          clearInterval(typeInterval)
        }
      }, 50) // 50ms per character for smooth typing

      return () => clearInterval(typeInterval)
    }, 1500) // Wait for other animations to complete

    return () => clearTimeout(startDelay)
  }, [currentSnark])

  const loadUserData = async () => {
    try {
      const entriesResponse = await api.getEntries(1, 100)
      if (entriesResponse.success && entriesResponse.data) {
        const entriesData = entriesResponse.data.data || entriesResponse.data
        if (entriesData.entries) {
          setEntries(entriesData.entries)
          generateInsights(entriesData.entries)
        }
      }
    } catch (error) {
      console.error('Failed to load user data:', error)
    }
  }

  const generateInsights = (entries: any[]) => {
    const insightsList: string[] = []
    
    if (entries.length > 0) {
      // Total words
      const totalWords = entries.reduce((sum, entry) => sum + (entry.word_count || 0), 0)
      insightsList.push(`<span class="text-pink-400">${totalWords.toLocaleString()}</span> words captured in your journey`)
      
      // Longest entry
      const longestEntry = entries.reduce((max, entry) => 
        (entry.word_count || 0) > (max.word_count || 0) ? entry : max
      )
      if (longestEntry.word_count > 0) {
        insightsList.push(`Your longest reflection was <span class="text-pink-400">${longestEntry.word_count}</span> words`)
      }
      
      // Favorite day
      const dayFrequency: { [key: string]: number } = {}
      entries.forEach(entry => {
        const day = format(new Date(entry.timestamp), 'EEEE')
        dayFrequency[day] = (dayFrequency[day] || 0) + 1
      })
      const favoriteDay = Object.entries(dayFrequency)
        .sort((a, b) => b[1] - a[1])[0]
      if (favoriteDay) {
        insightsList.push(`<span class="text-pink-400">${favoriteDay[0]}s</span> are your most reflective days`)
      }
      
      // Time preference
      const hourFrequency: { [key: number]: number } = {}
      entries.forEach(entry => {
        const hour = new Date(entry.timestamp).getHours()
        hourFrequency[hour] = (hourFrequency[hour] || 0) + 1
      })
      const favoriteHour = Object.entries(hourFrequency)
        .sort((a, b) => b[1] - a[1])[0]
      if (favoriteHour) {
        const hour = parseInt(favoriteHour[0])
        const timeOfDay = hour < 12 ? 'morning' : hour < 17 ? 'afternoon' : 'evening'
        insightsList.push(`You're most creative in the <span class="text-pink-400">${timeOfDay}</span>`)
      }
      
      // Average entry length
      const avgWords = Math.round(totalWords / entries.length)
      insightsList.push(`You average <span class="text-pink-400">${avgWords}</span> words per entry`)
      
      // Mood insights
      const moodCounts: { [key: string]: number } = {}
      entries.forEach(entry => {
        entry.mood_tags?.forEach((mood: string) => {
          moodCounts[mood] = (moodCounts[mood] || 0) + 1
        })
      })
      if (Object.keys(moodCounts).length > 0) {
        const topMood = Object.entries(moodCounts)
          .sort((a, b) => b[1] - a[1])[0]
        if (topMood) {
          insightsList.push(`Your dominant emotion: <span class="text-pink-400">${topMood[0]}</span>`)
        }
      }
    } else {
      insightsList.push('Your story begins with the first entry')
      insightsList.push('Every word you write becomes part of your journey')
      insightsList.push('Reflection is the key to understanding yourself')
    }
    
    setInsights(insightsList)
  }

  // Cycle through insights
  useEffect(() => {
    if (insights.length <= 1) return
    
    const interval = setInterval(() => {
      setCurrentInsightIndex(prev => (prev + 1) % insights.length)
    }, 4000)
    
    return () => clearInterval(interval)
  }, [insights])
  
  const viewModes = [
    {
      icon: FileText,
      title: "Raw Transcription",
      description: "Your exact words, unfiltered and authentic",
      gradient: "from-blue-500 to-blue-600",
      mode: "raw"
    },
    {
      icon: Pen,
      title: "Enhanced Style",
      description: "Improved grammar and tone while preserving your intent",
      gradient: "from-purple-500 to-pink-500",
      mode: "enhanced"
    },
    {
      icon: BookOpen,
      title: "Structured Summary",
      description: "Organized into coherent themes and key points",
      gradient: "from-emerald-500 to-teal-500",
      mode: "structured"
    }
  ]

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.2,
        delayChildren: 0.1
      }
    }
  }

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: {
        type: "spring",
        stiffness: 300,
        damping: 24
      }
    }
  }

  const cardVariants = {
    hidden: { y: 20, opacity: 0, scale: 0.9 },
    visible: {
      y: 0,
      opacity: 1,
      scale: 1,
      transition: {
        type: "spring",
        stiffness: 300,
        damping: 24
      }
    },
    hover: {
      y: -8,
      scale: 1.02,
      transition: {
        type: "spring",
        stiffness: 400,
        damping: 10
      }
    }
  }

  return (
    <div className="h-screen flex flex-col p-4 md:p-8 overflow-hidden relative">
      {/* Ambient Background with Floating Orbs */}
      <div className="absolute inset-0 pointer-events-none z-0 overflow-hidden">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1.5, ease: "easeOut" }}
          className="relative w-full h-full"
        >
          {/* Floating gradient orbs - avoiding top right clock area */}
          <motion.div
            animate={{ 
              scale: [1, 1.3, 1],
              opacity: [0.2, 0.4, 0.2],
              rotate: [0, 180, 360]
            }}
            transition={{ 
              duration: 8, 
              repeat: Infinity, 
              ease: "easeInOut" 
            }}
            className="absolute top-16 left-16 w-20 h-20 bg-gradient-to-r from-primary/30 to-blue-400/30 rounded-full blur-xl"
          />
          <motion.div
            animate={{ 
              scale: [1, 1.2, 1],
              opacity: [0.25, 0.45, 0.25],
              rotate: [0, -180, -360]
            }}
            transition={{ 
              duration: 10, 
              repeat: Infinity, 
              ease: "easeInOut",
              delay: 4
            }}
            className="absolute bottom-24 left-24 w-24 h-24 bg-gradient-to-tl from-cyan-400/25 to-indigo-400/25 rounded-full blur-xl"
          />
          <motion.div
            animate={{ 
              scale: [1, 1.4, 1],
              opacity: [0.2, 0.4, 0.2],
              rotate: [180, 0, -180]
            }}
            transition={{ 
              duration: 14, 
              repeat: Infinity, 
              ease: "easeInOut",
              delay: 1
            }}
            className="absolute top-1/2 left-1/3 w-18 h-18 bg-gradient-to-bl from-secondary/35 to-purple-400/35 rounded-full blur-xl"
          />
          <motion.div
            animate={{ 
              scale: [1, 1.6, 1],
              opacity: [0.15, 0.3, 0.15],
              rotate: [90, 270, 450]
            }}
            transition={{ 
              duration: 16, 
              repeat: Infinity, 
              ease: "easeInOut",
              delay: 6
            }}
            className="absolute bottom-1/4 left-1/4 w-22 h-22 bg-gradient-to-tr from-pink-400/30 to-cyan-400/30 rounded-full blur-xl"
          />
          <motion.div
            animate={{ 
              scale: [1, 1.1, 1],
              opacity: [0.3, 0.5, 0.3],
              rotate: [-90, 90, 270]
            }}
            transition={{ 
              duration: 6, 
              repeat: Infinity, 
              ease: "easeInOut",
              delay: 3
            }}
            className="absolute top-3/4 left-1/2 w-14 h-14 bg-gradient-to-r from-blue-400/35 to-primary/35 rounded-full blur-xl"
          />
        </motion.div>
      </div>
      <div className="max-w-6xl mx-auto w-full flex flex-col flex-1 justify-center">
        <motion.div 
          className="flex flex-col"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
      {/* Hero Section */}
      <motion.div className="text-center mb-16" variants={itemVariants}>
        <motion.h1 
          className="text-5xl md:text-6xl font-bold mb-6 bg-gradient-to-r from-white via-purple-400 to-blue-400 bg-clip-text text-transparent"
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.5 }}
        >
          Welcome to Echo Journal
        </motion.h1>
        <motion.p 
          className="text-gray-300 text-lg md:text-xl max-w-2xl mx-auto leading-relaxed"
          variants={itemVariants}
        >
          Type it, say it, mumble it at 2AM - Echo remembers, privately
        </motion.p>
      </motion.div>

      {/* Mode Cards */}
      <motion.div 
        className="grid md:grid-cols-3 gap-8 mb-16"
        variants={containerVariants}
      >
        {viewModes.map((mode) => (
          <motion.div
            key={mode.mode}
            variants={cardVariants}
            whileHover="hover"
            whileTap={{ scale: 0.95 }}
          >
            <Card 
              className="cursor-pointer h-full bg-card/50 backdrop-blur-sm border-border/50 hover:border-primary/30 transition-all duration-300 overflow-hidden group relative"
              onClick={() => navigate('/entries', { state: { previewMode: mode.mode } })}
            >
              {/* Gradient overlay */}
              <div className={`absolute inset-0 bg-gradient-to-br ${mode.gradient} opacity-0 group-hover:opacity-5 transition-opacity duration-300`} />
              
              {/* Shimmer effect */}
              <div className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/10 to-transparent group-hover:translate-x-full transition-transform duration-700" />
              
              <CardHeader className="pb-4 relative">
                <motion.div 
                  className={`w-16 h-16 rounded-2xl bg-gradient-to-br ${mode.gradient} flex items-center justify-center mb-6 shadow-lg shadow-primary/20 relative`}
                  whileHover={{ 
                    scale: 1.1,
                    rotate: 5
                  }}
                  transition={{ type: "spring", stiffness: 300, damping: 10 }}
                >
                  <mode.icon className="h-8 w-8 text-white" />
                  
                  {/* Static ring - no pulse */}
                  <div className={`absolute inset-0 rounded-2xl bg-gradient-to-br ${mode.gradient} opacity-10`} />
                </motion.div>
                
                <CardTitle className="text-xl font-bold text-white group-hover:text-primary transition-colors duration-300">
                  {mode.title}
                </CardTitle>
                <CardDescription className="text-gray-300 text-base leading-relaxed">
                  {mode.description}
                </CardDescription>
              </CardHeader>
              <CardContent className="pt-0">
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </motion.div>

      {/* Top Right Clock - NO CARD */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: 0.8 }}
        className="absolute top-4 right-4 md:top-8 md:right-8 z-30 text-right"
      >
        {/* Time Display - Time and AM/PM on same line */}
        <div className="flex items-baseline justify-end gap-2 mb-3">
          <div className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-white via-purple-400 to-pink-400 bg-clip-text text-transparent font-mono w-28 text-right">
            {format(currentTime, 'hh:mm')}
          </div>
          <motion.div 
            className="text-lg font-medium text-purple-300 w-8 text-left"
            animate={{ 
              opacity: [0.6, 1, 0.6]
            }}
            transition={{ 
              duration: 2, 
              repeat: Infinity, 
              ease: "easeInOut" 
            }}
          >
            {format(currentTime, 'a')}
          </motion.div>
        </div>

        {/* Snarky Comment - Typewriter Effect */}
        <div className="w-[32rem] min-h-[1.5rem]">
          <p className="text-gray-300 text-sm italic text-right whitespace-nowrap">
            "{displayedSnark}
            {isTyping && (
              <motion.span
                animate={{ opacity: [1, 0] }}
                transition={{ duration: 0.8, repeat: Infinity }}
                className="text-pink-400"
              >
                |
              </motion.span>
            )}"
          </p>
        </div>
      </motion.div>

      {/* Rolling Insights */}
      <div className="absolute bottom-12 md:bottom-16 left-0 right-0 z-40">
        <div className="max-w-6xl mx-auto px-4 md:px-8">
          <div className="text-center">
            <AnimatePresence mode="wait">
              {insights.length > 0 && (
                <motion.p
                  key={currentInsightIndex}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.3 }}
                  className="text-gray-300 text-lg max-w-2xl mx-auto leading-relaxed cursor-pointer select-none"
                  onClick={() => setCurrentInsightIndex(prev => (prev + 1) % insights.length)}
                  onMouseDown={(e) => {
                    const startX = e.clientX
                    const handleMouseMove = (moveEvent: MouseEvent) => {
                      const deltaX = moveEvent.clientX - startX
                      if (Math.abs(deltaX) > 50) {
                        if (deltaX > 0) {
                          setCurrentInsightIndex(prev => (prev + 1) % insights.length)
                        } else {
                          setCurrentInsightIndex(prev => prev === 0 ? insights.length - 1 : prev - 1)
                        }
                        document.removeEventListener('mousemove', handleMouseMove)
                        document.removeEventListener('mouseup', handleMouseUp)
                      }
                    }
                    const handleMouseUp = () => {
                      document.removeEventListener('mousemove', handleMouseMove)
                      document.removeEventListener('mouseup', handleMouseUp)
                    }
                    document.addEventListener('mousemove', handleMouseMove)
                    document.addEventListener('mouseup', handleMouseUp)
                  }}
                  title="Click or drag to navigate insights"
                  dangerouslySetInnerHTML={{ __html: insights[currentInsightIndex] }}
                />
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
        </motion.div>
      </div>
    </div>
  )
}

export default HomePage