import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { format } from 'date-fns'
import { useNavigate } from 'react-router-dom'
import SignupModal from '@/components/SignupModal'
import LoginModal from '@/components/LoginModal'
import SuccessModal from '@/components/SuccessModal'

// Typewriter Text Component (from TalkToYourDiaryPage)
interface TypewriterTextProps {
  text: string
  delay?: number
  className?: string
}

function TypewriterText({ text, delay = 0, className = '' }: TypewriterTextProps) {
  const [displayedText, setDisplayedText] = useState('')
  const [currentIndex, setCurrentIndex] = useState(0)
  const [startTyping, setStartTyping] = useState(false)

  useEffect(() => {
    const timer = setTimeout(() => {
      setStartTyping(true)
    }, delay * 1000)

    return () => clearTimeout(timer)
  }, [delay])

  useEffect(() => {
    if (!startTyping) return

    if (currentIndex < text.length) {
      const timer = setTimeout(() => {
        setDisplayedText(text.slice(0, currentIndex + 1))
        setCurrentIndex(currentIndex + 1)
      }, 50) // 50ms per character

      return () => clearTimeout(timer)
    }
  }, [currentIndex, text, startTyping])

  return (
    <motion.p 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: startTyping ? 1 : 0, y: 0 }}
      transition={{ duration: 0.3 }}
      className={className}
    >
      {displayedText}
      {currentIndex < text.length && (
        <motion.span
          animate={{ opacity: [1, 0] }}
          transition={{ duration: 0.8, repeat: Infinity }}
          className="text-primary"
        >
          |
        </motion.span>
      )}
    </motion.p>
  )
}

function LandingPage() {
  const navigate = useNavigate()
  const [showSignupModal, setShowSignupModal] = useState(false)
  const [showSigninModal, setShowSigninModal] = useState(false)
  const [currentTime, setCurrentTime] = useState(new Date())
  const [showSuccessModal, setShowSuccessModal] = useState(false)
  const [successData, setSuccessData] = useState({ title: '', message: '' })

  const handleSignupSuccess = (user: any) => {
    console.log('Signup successful:', user)
    setSuccessData({
      title: 'Welcome to Echo!',
      message: `Your account has been created successfully, ${user.display_name}! Get ready to capture your thoughts.`
    })
    setShowSuccessModal(true)
    
    // Navigate to home page after success modal
    setTimeout(() => {
      navigate('/', { replace: true })
      window.location.reload()
    }, 3000)
  }

  const handleLoginSuccess = (user: any) => {
    console.log('Login successful:', user)
    setSuccessData({
      title: 'Welcome Back!',
      message: `Good to see you again, ${user.display_name}! Let's dive back into your thoughts.`
    })
    setShowSuccessModal(true)
    
    // Navigate to home page after success modal
    setTimeout(() => {
      navigate('/', { replace: true })
      window.location.reload()
    }, 3000)
  }

  const handleSuccessModalClose = () => {
    setShowSuccessModal(false)
    // Navigate to home page immediately when manually closed
    navigate('/', { replace: true })
    window.location.reload()
  }

  // Animation variants - EXACT same as HomePage
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

  // Clock update effect - same as HomePage
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date())
    }, 1000)
    
    return () => clearInterval(timer)
  }, [])

  return (
    <div className="min-h-screen bg-background text-foreground relative overflow-hidden">
      <div className="relative z-10 min-h-screen flex flex-col">
      {/* Background Elements - Same as HomePage */}
      <motion.div
        animate={{
          x: [0, 30, 0],
          y: [0, -20, 0],
        }}
        transition={{
          duration: 20,
          repeat: Infinity,
          ease: "linear"
        }}
        className="absolute top-16 left-16 w-20 h-20 bg-gradient-to-r from-primary/30 to-blue-400/30 rounded-full blur-xl"
      />
      
      <motion.div
        animate={{
          x: [0, -25, 0],
          y: [0, 25, 0],
        }}
        transition={{
          duration: 25,
          repeat: Infinity,
          ease: "linear"
        }}
        className="absolute bottom-24 left-24 w-24 h-24 bg-gradient-to-tl from-cyan-400/25 to-indigo-400/25 rounded-full blur-xl"
      />

      <motion.div
        animate={{
          x: [0, 20, 0],
          y: [0, -30, 0],
        }}
        transition={{
          duration: 18,
          repeat: Infinity,
          ease: "linear"
        }}
        className="absolute top-1/2 left-1/3 w-18 h-18 bg-gradient-to-bl from-secondary/35 to-purple-400/35 rounded-full blur-xl"
      />

      <motion.div
        animate={{
          x: [0, -15, 0],
          y: [0, 20, 0],
        }}
        transition={{
          duration: 22,
          repeat: Infinity,
          ease: "linear"
        }}
        className="absolute bottom-1/4 left-1/4 w-22 h-22 bg-gradient-to-tr from-pink-400/30 to-cyan-400/30 rounded-full blur-xl"
      />

      <motion.div
        animate={{
          x: [0, 25, 0],
          y: [0, -25, 0],
        }}
        transition={{
          duration: 28,
          repeat: Infinity,
          ease: "linear"
        }}
        className="absolute top-3/4 left-1/2 w-14 h-14 bg-gradient-to-r from-blue-400/35 to-primary/35 rounded-full blur-xl"
      />

      <div className="max-w-6xl mx-auto w-full flex flex-col flex-1 justify-center px-4">
        <motion.div 
          className="flex flex-col"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          {/* Auth Card */}
          <motion.div className="text-center" variants={itemVariants}>
            <Card className="bg-card/60 backdrop-blur-xl border border-border/60 mx-auto max-w-3xl relative overflow-hidden shadow-2xl">
              <div className="absolute inset-0 bg-gradient-to-br from-primary/10 via-secondary/5 to-purple-600/10" />
              {/* Additional glow effect */}
              <div className="absolute inset-0 bg-gradient-to-tr from-blue-500/5 via-transparent to-purple-500/5 blur-xl" />
              <CardContent className="p-16 relative">
                
                {/* Echo Title - Much Larger - EXACT same classes as HomePage but bigger size */}
                <motion.h1 
                  className="text-7xl md:text-8xl font-bold mb-8 bg-gradient-to-r from-white via-purple-400 to-blue-400 bg-clip-text text-transparent"
                  initial={{ scale: 0.9, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ duration: 0.5 }}
                >
                  Echo
                </motion.h1>
                
                {/* Typewriter Tagline */}
                <div className="h-20 flex items-center justify-center mb-16">
                  <TypewriterText 
                    text="A quiet space... for your loud thoughts"
                    delay={0.5}
                    className="text-gray-300 text-xl md:text-2xl max-w-2xl mx-auto leading-relaxed"
                  />
                </div>

                {/* Auth Buttons - Enhanced design */}
                <motion.div 
                  className="flex flex-col sm:flex-row gap-6 justify-center items-center"
                  initial={{ opacity: 0, y: 30 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: 1.8 }}
                >
                  {/* Sign Up Button - Primary */}
                  <motion.button
                    onClick={() => setShowSignupModal(true)}
                    whileHover={{ scale: 1.02, y: -2 }}
                    whileTap={{ scale: 0.98 }}
                    className="group relative overflow-hidden px-10 py-4 rounded-2xl font-bold text-lg shadow-2xl transition-all duration-300 min-w-[180px]"
                    style={{
                      background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.8) 0%, rgba(139, 92, 246, 0.8) 100%)',
                      boxShadow: '0 10px 30px rgba(99, 102, 241, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.2)'
                    }}
                  >
                    {/* Animated background */}
                    <div className="absolute inset-0 bg-gradient-to-r from-indigo-600/20 to-purple-600/20 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                    {/* Shimmer effect */}
                    <div className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/20 to-transparent group-hover:translate-x-full transition-transform duration-700" />
                    <span className="relative z-10 text-white drop-shadow-sm">
                      Create Account
                    </span>
                  </motion.button>
                  
                  {/* Sign In Button - Secondary */}
                  <motion.button
                    onClick={() => setShowSigninModal(true)}
                    whileHover={{ scale: 1.02, y: -2 }}
                    whileTap={{ scale: 0.98 }}
                    className="group relative overflow-hidden px-10 py-4 rounded-2xl font-bold text-lg shadow-2xl transition-all duration-300 min-w-[180px] bg-card/80 backdrop-blur-sm border-2 border-primary/30 text-white hover:border-primary/50"
                  >
                    {/* Animated background */}
                    <div className="absolute inset-0 bg-gradient-to-r from-primary/5 to-secondary/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                    {/* Shimmer effect */}
                    <div className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/10 to-transparent group-hover:translate-x-full transition-transform duration-700" />
                    <span className="relative z-10 drop-shadow-sm">
                      Sign In
                    </span>
                  </motion.button>
                </motion.div>
              </CardContent>
            </Card>
          </motion.div>
        </motion.div>
      </div>

      {/* Top Right Clock - Same as HomePage */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: 0.8 }}
        className="absolute top-4 right-4 md:top-8 md:right-8 z-30 text-right"
      >
        {/* Time Display */}
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
      </motion.div>
      </div>

      {/* Modals */}
      <SignupModal
        isOpen={showSignupModal}
        onClose={() => setShowSignupModal(false)}
        onSuccess={handleSignupSuccess}
      />

      <LoginModal
        isOpen={showSigninModal}
        onClose={() => setShowSigninModal(false)}
        onSuccess={handleLoginSuccess}
      />

      <SuccessModal
        isOpen={showSuccessModal}
        title={successData.title}
        message={successData.message}
        onClose={handleSuccessModalClose}
        autoCloseMs={3000}
      />
    </div>
  )
}

export default LandingPage