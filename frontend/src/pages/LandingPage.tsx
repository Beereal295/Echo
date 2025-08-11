import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { format } from 'date-fns'
import SignupModal, { SignupData } from '@/components/SignupModal'
import LoginModal, { LoginData } from '@/components/LoginModal'

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
  const [showSignupModal, setShowSignupModal] = useState(false)
  const [showSigninModal, setShowSigninModal] = useState(false)
  const [currentTime, setCurrentTime] = useState(new Date())

  // Mock handlers for now - these will be connected to backend later
  const handleSignup = async (data: SignupData) => {
    console.log('Signup data:', data)
    // TODO: Connect to backend auth service
    alert(`Welcome ${data.name}! Account creation coming soon.\nRecovery phrase: "${data.recoveryPhrase}"\nEmergency key generated: ${data.emergencyKey ? 'Yes' : 'No'}`)
    setShowSignupModal(false)
  }

  const handleLogin = async (data: LoginData) => {
    console.log('Login data:', data)
    // TODO: Connect to backend auth service
    const method = data.password ? 'password' : data.recoveryPhrase ? 'recovery phrase' : 'emergency key'
    alert(`Welcome back ${data.name}! Login with ${method} coming soon.`)
    setShowSigninModal(false)
  }

  const handleForgotPassword = () => {
    // Recovery functionality is handled within LoginModal
    console.log('Password recovery initiated')
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

      <div className="max-w-6xl mx-auto w-full flex flex-col flex-1 justify-center">
        <motion.div 
          className="flex flex-col"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          {/* Auth Card */}
          <motion.div className="text-center" variants={itemVariants}>
            <Card className="bg-card/50 backdrop-blur-sm border-border/50 mx-auto max-w-2xl relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-secondary/5" />
              <CardContent className="p-12 relative">
                
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
                <div className="h-16 flex items-center justify-center mb-12">
                  <TypewriterText 
                    text="A quiet space... for your loud thoughts"
                    delay={0.5}
                    className="text-gray-300 text-xl md:text-2xl max-w-2xl mx-auto leading-relaxed"
                  />
                </div>

                {/* Auth Buttons - Separate animation with delay */}
                <motion.div 
                  className="flex flex-col sm:flex-row gap-16 justify-center items-center"
                  initial={{ opacity: 0, y: 30 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: 1.8 }}
                >
          <motion.button
            onClick={() => setShowSignupModal(true)}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="relative overflow-hidden group px-8 py-4 rounded-xl font-semibold shadow-lg hover:shadow-xl transition-all duration-300 cursor-pointer inline-flex items-center justify-center bg-primary/10 border border-primary/20 text-primary hover:bg-primary/20"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-primary/10 to-secondary/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
            <span className="relative z-10 text-primary font-semibold group-hover:text-primary transition-colors duration-300">
              Sign Up
            </span>
          </motion.button>
          
          <motion.button
            onClick={() => setShowSigninModal(true)}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="relative overflow-hidden group px-8 py-4 rounded-xl font-semibold shadow-lg hover:shadow-xl transition-all duration-300 cursor-pointer inline-flex items-center justify-center bg-primary/10 border border-primary/20 text-primary hover:bg-primary/20"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-primary/10 to-secondary/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
            <span className="relative z-10 text-primary font-semibold group-hover:text-primary transition-colors duration-300">
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
        onSubmit={handleSignup}
      />

      <LoginModal
        isOpen={showSigninModal}
        onClose={() => setShowSigninModal(false)}
        onSubmit={handleLogin}
        onForgotPassword={handleForgotPassword}
      />
    </div>
  )
}

export default LandingPage