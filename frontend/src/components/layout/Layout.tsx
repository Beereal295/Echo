import { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { 
  Plus, 
  FileText, 
  MessageSquare, 
  Diamond, 
  Calendar, 
  Settings,
  Flame,
  Sparkles,
  ChevronLeft,
  ChevronRight
} from 'lucide-react'
import { api } from '@/lib/api'

interface LayoutProps {
  children: React.ReactNode
}

function Layout({ children }: LayoutProps) {
  const [showPatterns, setShowPatterns] = useState(false)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => {
    // Load collapsed state from localStorage
    const saved = localStorage.getItem('sidebarCollapsed')
    return saved ? JSON.parse(saved) : false
  })
  const [dailyStreak, setDailyStreak] = useState(0)
  const [streakLoading, setStreakLoading] = useState(true)
  const location = useLocation()

  // Calculate daily streak from entries
  const calculateDailyStreak = async () => {
    try {
      setStreakLoading(true)
      // Use the dedicated streak endpoint that has no pagination limits
      const response = await api.getDailyStreak()
      
      if (response.success && response.data) {
        console.log('Streak data from server:', response.data)
        setDailyStreak(response.data.streak)
      } else {
        console.error('Failed to get streak data:', response.error)
        setDailyStreak(0)
      }
    } catch (error) {
      console.error('Failed to calculate daily streak:', error)
      setDailyStreak(0)
    } finally {
      setStreakLoading(false)
    }
  }

  useEffect(() => {
    // Check if pattern threshold is met
    const checkPatternThreshold = async () => {
      try {
        const response = await api.checkPatternThreshold()
        if (response.success && response.data && response.data.data) {
          setShowPatterns(response.data.data.threshold_met)
        }
      } catch (error) {
        console.error('Failed to check pattern threshold:', error)
      }
    }
    
    // Initial checks
    checkPatternThreshold()
    calculateDailyStreak()
    
    // Listen for settings updates
    const handleSettingsUpdate = () => {
      checkPatternThreshold()
      calculateDailyStreak()
    }
    
    window.addEventListener('settingsUpdated', handleSettingsUpdate)
    
    // Check periodically to update when new entries are added
    const interval = setInterval(() => {
      checkPatternThreshold()
      calculateDailyStreak()
    }, 60000) // Check every minute
    
    return () => {
      clearInterval(interval)
      window.removeEventListener('settingsUpdated', handleSettingsUpdate)
    }
  }, [])

  // Save collapsed state to localStorage
  useEffect(() => {
    localStorage.setItem('sidebarCollapsed', JSON.stringify(sidebarCollapsed))
  }, [sidebarCollapsed])

  const toggleSidebar = () => {
    setSidebarCollapsed(!sidebarCollapsed)
  }

  const navItems = [
    {
      path: '/new',
      icon: Plus,
      label: 'New Entry',
      alwaysShow: true,
      gradient: true
    },
    {
      path: '/entries',
      icon: FileText,
      label: 'View Entries',
      alwaysShow: true
    },
    {
      path: '/talk',
      icon: MessageSquare,
      label: 'Talk to Your Diary',
      alwaysShow: true
    },
    {
      path: '/patterns',
      icon: Diamond,
      label: 'Pattern Insights',
      alwaysShow: showPatterns,
      special: true
    },
    {
      path: '/memories',
      icon: Calendar,
      label: 'Memories',
      alwaysShow: true
    },
    {
      path: '/settings',
      icon: Settings,
      label: 'Settings',
      alwaysShow: true
    }
  ]

  return (
    <TooltipProvider delayDuration={0}>
      <div className="flex h-screen bg-background overflow-hidden relative">
      {/* Left Sidebar - Responsive with Glass Effect */}
      <motion.aside 
        initial={{ x: -300 }}
        animate={{ 
          x: 0,
          transition: {
            duration: 0.4,
            ease: "easeOut"
          }
        }}
        className={`${
          sidebarCollapsed ? 'w-20' : 'w-60'
        } border-r border-border/50 bg-card/90 backdrop-blur-xl flex flex-col relative transition-[width] duration-200 ease-out`}
      >
        {/* Ambient gradient overlay */}
        <motion.div 
          className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-accent/5 pointer-events-none"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1, delay: 0.5 }}
        />
        
        {/* Logo/Title */}
        <div className="px-4 py-3 h-16 border-b border-border/50 relative flex items-center transition-all duration-200">
          {sidebarCollapsed ? (
            <Tooltip>
              <TooltipTrigger asChild>
                <Link to="/" className="block">
                  <motion.div
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className="flex items-center justify-center w-full"
                  >
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg">
                      <Sparkles className="w-4 h-4 text-white drop-shadow-md" />
                    </div>
                  </motion.div>
                </Link>
              </TooltipTrigger>
              <TooltipContent side="right" sideOffset={20} className="z-[200]">
                <p>Echo Journal</p>
              </TooltipContent>
            </Tooltip>
          ) : (
            <Link to="/" className="block">
              <motion.div
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="flex items-center space-x-3 w-full"
              >
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg">
                  <Sparkles className="w-4 h-4 text-white drop-shadow-md" />
                </div>
                <AnimatePresence mode="wait">
                  <motion.h1 
                    key="logo-text"
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -10 }}
                    transition={{ duration: 0.2, ease: "easeOut" }}
                    className="font-bold text-xl bg-gradient-to-r from-white via-purple-400 to-blue-400 bg-clip-text text-transparent whitespace-nowrap"
                  >
                    Echo Journal
                  </motion.h1>
                </AnimatePresence>
              </motion.div>
            </Link>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 relative">
          <div className="space-y-2">
            {navItems.map((item, index) => {
              if (!item.alwaysShow) return null
              
              const isActive = location.pathname === item.path
              
              const buttonContent = (
                <Button 
                  className={`w-full ${sidebarCollapsed ? 'justify-center px-2' : 'justify-start'} relative overflow-hidden group transition-all duration-200 ${
                    isActive 
                      ? 'bg-primary/10 text-primary border border-primary/20 shadow-lg shadow-primary/10 hover:bg-primary/20 hover:text-primary' 
                      : 'hover:bg-muted/50 hover:shadow-md text-white hover:text-white'
                  }`}
                  variant="ghost"
                >
                      {/* Animated background for active state */}
                      {isActive && (
                        <motion.div
                          layoutId="activeNavBg"
                          className="absolute inset-0 bg-gradient-to-r from-primary/10 to-secondary/10"
                          initial={false}
                          transition={{ type: "spring", stiffness: 500, damping: 30 }}
                        />
                      )}
                      
                      <div className={`relative flex items-center ${sidebarCollapsed ? 'justify-center' : ''}`}>
                        <item.icon className={`${sidebarCollapsed ? '' : 'mr-3'} h-5 w-5 transition-colors duration-200 ${
                          isActive ? 'text-primary group-hover:text-primary' : 'text-white group-hover:text-white'
                        } ${item.special ? 'text-primary' : ''}`} />
                        <AnimatePresence mode="wait">
                          {!sidebarCollapsed && (
                            <motion.span 
                              key={`text-${index}`}
                              initial={{ opacity: 0, x: -10 }}
                              animate={{ opacity: 1, x: 0 }}
                              exit={{ opacity: 0, x: -10 }}
                              transition={{ duration: 0.2, ease: "easeOut" }}
                              className={`text-[15px] whitespace-nowrap ${
                                isActive ? 'text-primary font-medium group-hover:text-primary' : 'text-white group-hover:text-white'
                              }`}
                            >
                              {item.label}
                            </motion.span>
                          )}
                        </AnimatePresence>
                            
                      </div>
                </Button>
              )
              
              return (
                <div key={item.path}>
                  {sidebarCollapsed ? (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Link to={item.path}>
                          {buttonContent}
                        </Link>
                      </TooltipTrigger>
                      <TooltipContent side="right" sideOffset={20} className="z-[200]">
                        <p>{item.label}</p>
                      </TooltipContent>
                    </Tooltip>
                  ) : (
                    <Link to={item.path}>
                      {buttonContent}
                    </Link>
                  )}
                </div>
              )
            })}
          </div>
        </nav>

        {/* Toggle Button */}
        <div className="px-4 py-3 border-t border-border/50">
          {sidebarCollapsed ? (
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  onClick={toggleSidebar}
                  variant="ghost"
                  size="sm"
                  className="w-full justify-center hover:bg-muted/50 text-white hover:text-white"
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="right" sideOffset={20} className="z-[200]">
                <p>Expand sidebar</p>
              </TooltipContent>
            </Tooltip>
          ) : (
            <Button
              onClick={toggleSidebar}
              variant="ghost"
              size="sm"
              className="w-full justify-start hover:bg-muted/50 text-white hover:text-white"
            >
              <ChevronLeft className="h-4 w-4 mr-2" />
              <AnimatePresence mode="wait">
                <motion.span 
                  key="collapse-text"
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -10 }}
                  transition={{ duration: 0.2, ease: "easeOut" }}
                  className="text-[15px] whitespace-nowrap"
                >
                  Collapse
                </motion.span>
              </AnimatePresence>
            </Button>
          )}
        </div>

        {/* Bottom Section - Streak */}
        <div className="px-4 py-3 border-t border-border/50 min-h-[60px] flex items-center">
          {sidebarCollapsed ? (
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="w-full flex justify-center">
                  <Badge className="bg-primary/10 text-primary border border-primary/20 font-medium hover:bg-primary/20 hover:text-primary transition-colors duration-300 group cursor-pointer">
                    <motion.div
                      animate={dailyStreak > 0 ? {
                        scale: [1, 1.1, 1],
                        rotate: [0, -2, 2, 0]
                      } : {}}
                      transition={{
                        duration: 2,
                        repeat: dailyStreak > 0 ? Infinity : 0,
                        ease: "easeInOut"
                      }}
                    >
                      <Flame className={`h-3 w-3 transition-all duration-300 ${
                        dailyStreak > 0 
                          ? 'text-orange-400 drop-shadow-sm filter brightness-125' 
                          : 'text-gray-400'
                      }`} />
                    </motion.div>
                  </Badge>
                </div>
              </TooltipTrigger>
              <TooltipContent side="right" sideOffset={20} className="z-[200]">
                <p>Daily Streak: {streakLoading ? '...' : `${dailyStreak} ${dailyStreak === 1 ? 'day' : 'days'}`}</p>
              </TooltipContent>
            </Tooltip>
          ) : (
            <div className="w-full flex items-center justify-between">
              <AnimatePresence mode="wait">
                <motion.span 
                  key="streak-text"
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -10 }}
                  transition={{ duration: 0.2, ease: "easeOut" }}
                  className="text-gray-300 font-medium text-[15px] whitespace-nowrap"
                >
                  Daily Streak
                </motion.span>
              </AnimatePresence>
              <Badge className="bg-primary/10 text-primary border border-primary/20 font-medium hover:bg-primary/20 hover:text-primary transition-colors duration-300 group">
                <motion.div
                  animate={dailyStreak > 0 ? {
                    scale: [1, 1.1, 1],
                    rotate: [0, -2, 2, 0]
                  } : {}}
                  transition={{
                    duration: 2,
                    repeat: dailyStreak > 0 ? Infinity : 0,
                    ease: "easeInOut"
                  }}
                  className="mr-1"
                >
                  <Flame className={`h-3 w-3 transition-all duration-300 ${
                    dailyStreak > 0 
                      ? 'text-orange-400 drop-shadow-sm filter brightness-125' 
                      : 'text-gray-400'
                  }`} />
                </motion.div>
                <AnimatePresence mode="wait">
                  <motion.span 
                    key={`streak-count-${dailyStreak}`}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -10 }}
                    transition={{ duration: 0.2, ease: "easeOut" }}
                    className="whitespace-nowrap"
                  >
                    {streakLoading ? '...' : `${dailyStreak} ${dailyStreak === 1 ? 'day' : 'days'}`}
                  </motion.span>
                </AnimatePresence>
              </Badge>
            </div>
          )}
        </div>
      </motion.aside>

      {/* Main Content Area */}
      <main className="flex-1 overflow-hidden relative bg-background">
        <motion.div
          key={location.pathname}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{ duration: 0.3 }}
          className="h-full overflow-auto"
        >
          {children}
        </motion.div>
      </main>

      {/* Floating Plus Button with Enhanced Design - Only show on homepage */}
      <AnimatePresence>
        {location.pathname === '/' && (
          <motion.div
            initial={{ scale: 0, rotate: -180 }}
            animate={{ 
              scale: [1, 1.1, 1], 
              rotate: 0 
            }}
            exit={{ scale: 0, rotate: -180, opacity: 0 }}
            transition={{ 
              scale: { duration: 2.5, repeat: Infinity, ease: "easeInOut", delay: 2 },
              rotate: { type: "spring", stiffness: 260, damping: 20, delay: 1 },
              exit: { duration: 0.3 }
            }}
            className="fixed bottom-4 right-4 md:bottom-8 md:right-8 z-50"
          >
            <Link to="/new" className="focus:outline-none outline-none">
              <motion.div
                whileHover={{ rotate: 90, scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                transition={{ type: "spring", stiffness: 400, damping: 17 }}
                className="flex items-center justify-center cursor-pointer focus:outline-none outline-none"
              >
                <Plus className="h-16 w-16 stroke-2 text-white" />
              </motion.div>
            </Link>
          </motion.div>
        )}
      </AnimatePresence>
      </div>
    </TooltipProvider>
  )
}

export default Layout