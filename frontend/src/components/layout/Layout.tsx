import { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  Plus, 
  FileText, 
  MessageSquare, 
  Diamond, 
  Calendar, 
  Settings,
  Flame,
  Sparkles
} from 'lucide-react'

interface LayoutProps {
  children: React.ReactNode
}

function Layout({ children }: LayoutProps) {
  const [showPatterns, setShowPatterns] = useState(false)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const location = useLocation()

  useEffect(() => {
    // Check if user has 30+ entries
    const checkEntryCount = async () => {
      try {
        // For demo purposes, patterns are hidden by default
        // TODO: Replace with actual API call to check entry count
        // const response = await api.getEntryCount()
        // if (response.data.total_entries >= 30) {
        //   setShowPatterns(true)
        // }
      } catch (error) {
        console.error('Failed to check entry count:', error)
      }
    }
    
    checkEntryCount()

    // Handle responsive sidebar collapse on smaller screens
    const handleResize = () => {
      if (window.innerWidth < 1024) {
        setSidebarCollapsed(true)
      } else {
        setSidebarCollapsed(false)
      }
    }

    handleResize()
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

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
    <div className="flex h-screen bg-background overflow-hidden">
      {/* Left Sidebar - Responsive with Glass Effect */}
      <motion.aside 
        initial={{ x: -256, opacity: 0 }}
        animate={{ 
          x: 0, 
          opacity: 1,
          width: sidebarCollapsed ? 80 : 256
        }}
        transition={{ 
          duration: 0.6, 
          ease: "easeOut",
          delay: 0.2
        }}
        className={`${
          sidebarCollapsed ? 'w-20' : 'w-64'
        } border-r border-border/50 bg-card/90 backdrop-blur-xl flex flex-col relative transition-all duration-300`}
      >
        {/* Ambient gradient overlay */}
        <motion.div 
          className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-accent/5 pointer-events-none"
          animate={{ 
            opacity: [0.3, 0.6, 0.3]
          }}
          transition={{ 
            duration: 4, 
            repeat: Infinity, 
            ease: "easeInOut" 
          }}
        />
        
        {/* Logo/Title */}
        <div className={`${sidebarCollapsed ? 'p-4' : 'p-6'} border-b border-border/50 relative transition-all duration-300`}>
          <Link to="/" className="block">
            <motion.div
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className={`flex items-center ${sidebarCollapsed ? 'justify-center' : 'space-x-3'}`}
            >
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-secondary flex items-center justify-center shadow-lg">
                <Sparkles className="w-4 h-4" style={{color: 'white'}} />
              </div>
              {!sidebarCollapsed && (
                <h1 className="font-bold text-xl bg-gradient-to-r from-white via-purple-400 to-blue-400 bg-clip-text text-transparent">
                  Echo Journal
                </h1>
              )}
            </motion.div>
          </Link>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 relative">
          <div className="space-y-2">
            {navItems.map((item, index) => {
              if (!item.alwaysShow) return null
              
              const isActive = location.pathname === item.path
              
              return (
                <div key={item.path}>
                  <Link to={item.path}>
                    <Button 
                      className={`w-full ${sidebarCollapsed ? 'justify-center px-2' : 'justify-start'} relative overflow-hidden group transition-all duration-300 ${
                        isActive 
                          ? 'bg-primary/10 text-primary border border-primary/20 shadow-lg shadow-primary/10' 
                          : 'hover:bg-muted/50 hover:scale-[1.02] hover:shadow-md text-white hover:text-white'
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
                        <item.icon className={`${sidebarCollapsed ? '' : 'mr-3'} h-5 w-5 transition-all duration-300 ${
                          isActive ? 'text-primary' : 'text-white'
                        } ${item.special ? 'text-primary' : ''}`} />
                        {!sidebarCollapsed && (
                          <>
                            <span className={`transition-all duration-300 ${
                              isActive ? 'text-primary font-medium' : 'text-white'
                            }`}>
                              {item.label}
                            </span>
                            
                            {item.special && showPatterns && (
                              <motion.div
                                initial={{ scale: 0, rotate: -180 }}
                                animate={{ scale: 1, rotate: 0 }}
                                className="ml-auto"
                              >
                                <Badge className="bg-primary/20 text-primary border-primary/30 text-xs">
                                  NEW
                                </Badge>
                              </motion.div>
                            )}
                          </>
                        )}
                      </div>
                    </Button>
                  </Link>
                </div>
              )
            })}
          </div>
        </nav>

        {/* Bottom Section - Streak */}
        <div className="p-4 border-t border-border/50 relative">
          {sidebarCollapsed ? (
            <div className="flex justify-center">
              <Badge className="bg-primary/10 text-primary border border-primary/20 font-medium hover:bg-primary/20 hover:text-primary transition-colors duration-300 group">
                <Flame className="h-3 w-3 text-primary group-hover:text-primary transition-colors duration-300" />
              </Badge>
            </div>
          ) : (
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-300 font-medium">Daily Streak</span>
              <Badge className="bg-primary/10 text-primary border border-primary/20 font-medium hover:bg-primary/20 hover:text-primary transition-colors duration-300 group">
                <Flame className="mr-1 h-3 w-3 text-primary group-hover:text-primary transition-colors duration-300" />
                0 days
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

      {/* Floating Plus Button with Enhanced Design - Only show on homepage and entries page */}
      <AnimatePresence>
        {(location.pathname === '/' || location.pathname === '/entries') && (
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
                <Plus className="h-16 w-16 stroke-2" style={{color: 'white'}} />
              </motion.div>
            </Link>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default Layout