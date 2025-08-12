import { useState, useEffect, useMemo } from 'react'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { format } from 'date-fns'
import SignupModal from '@/components/SignupModal'
import LoginModal from '@/components/LoginModal'
import SuccessModal from '@/components/SuccessModal'

function LandingPage() {
  const navigate = useNavigate()
  const [showSignupModal, setShowSignupModal] = useState(false)
  const [showSigninModal, setShowSigninModal] = useState(false)
  const [showSuccessModal, setShowSuccessModal] = useState(false)
  const [successData, setSuccessData] = useState({ title: '', message: '' })
  const [currentTime, setCurrentTime] = useState(new Date())
  const [timeOfDay, setTimeOfDay] = useState<'morning' | 'day' | 'evening' | 'night'>('day')
  
  // Generate fixed star positions once
  const stars = useMemo(() => {
    const staticStars = Array.from({ length: 30 }, (_, i) => ({
      id: `static-${i}`,
      left: Math.random() * 100,
      top: Math.random() * 100,
      size: Math.random() * 2,
      opacity: Math.random() * 0.6 + 0.4,
    }))
    
    const shimmerStars = Array.from({ length: 20 }, (_, i) => ({
      id: `shimmer-${i}`,
      left: Math.random() * 100,
      top: Math.random() * 100,
      duration: Math.random() * 6 + 6,
      delay: Math.random() * 12,
    }))
    
    return { staticStars, shimmerStars }
  }, []) // Empty dependency array means these positions never change

  const handleSignupSuccess = (user: any) => {
    console.log('Signup successful:', user)
    setSuccessData({
      title: 'Welcome to Echo!',
      message: `Your account has been created successfully, ${user.display_name}! Get ready to capture your thoughts.`
    })
    setShowSuccessModal(true)
    
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
    
    setTimeout(() => {
      navigate('/', { replace: true })
      window.location.reload()
    }, 3000)
  }

  const handleSuccessModalClose = () => {
    setShowSuccessModal(false)
    navigate('/', { replace: true })
    window.location.reload()
  }

  // Clock update effect
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date())
    }, 1000)
    
    return () => clearInterval(timer)
  }, [])

  // Determine time of day
  useEffect(() => {
    const hour = currentTime.getHours()
    if (hour >= 5 && hour < 12) {
      setTimeOfDay('morning')
    } else if (hour >= 12 && hour < 17) {
      setTimeOfDay('day')
    } else if (hour >= 17 && hour < 20) {
      setTimeOfDay('evening')
    } else {
      setTimeOfDay('night')
    }
  }, [currentTime])

  // Get gradient colors based on time
  const getSceneGradient = () => {
    switch (timeOfDay) {
      case 'morning':
        return 'from-orange-400 via-pink-400 to-purple-500'
      case 'day':
        return 'from-blue-400 via-cyan-400 to-purple-500'
      case 'evening':
        return 'from-orange-500 via-pink-500 to-purple-600'
      case 'night':
        return 'from-indigo-800 via-purple-800 to-pink-900'
      default:
        return 'from-purple-600 via-pink-500 to-orange-400'
    }
  }

  // Get sun/moon properties based on time
  const getCelestialBody = () => {
    switch (timeOfDay) {
      case 'morning':
        return { gradient: 'from-yellow-200 to-orange-300', size: 'w-16 h-16' }
      case 'day':
        return { gradient: 'from-yellow-100 to-yellow-300', size: 'w-14 h-14' }
      case 'evening':
        return { gradient: 'from-orange-300 to-red-400', size: 'w-16 h-16' }
      case 'night':
        return { gradient: 'from-gray-200 to-gray-400', size: 'w-12 h-12' }
      default:
        return { gradient: 'from-yellow-200 to-orange-300', size: 'w-16 h-16' }
    }
  }

  const celestialBody = getCelestialBody()

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 via-purple-900 to-slate-900 text-foreground relative overflow-hidden">
      {/* Static stars with subtle shimmer */}
      <div className="absolute inset-0 pointer-events-none">
        {/* Layer 1: Static bright stars */}
        {stars.staticStars.map((star) => (
          <div
            key={star.id}
            className="absolute bg-white rounded-full"
            style={{
              left: `${star.left}%`,
              top: `${star.top}%`,
              width: `${star.size}px`,
              height: `${star.size}px`,
              opacity: star.opacity,
            }}
          />
        ))}
        
        {/* Layer 2: Subtle shimmering stars */}
        {stars.shimmerStars.map((star) => (
          <motion.div
            key={star.id}
            className="absolute w-1 h-1 bg-white rounded-full"
            style={{
              left: `${star.left}%`,
              top: `${star.top}%`,
            }}
            animate={{
              opacity: [0.6, 0.9, 0.6],
              scale: [1, 1.2, 1],
            }}
            transition={{
              duration: star.duration,
              repeat: Infinity,
              delay: star.delay,
              ease: "easeInOut",
            }}
          />
        ))}
        
        {/* Shooting stars */}
        {[...Array(3)].map((_, i) => (
          <motion.div
            key={`shooting-${i}`}
            className="absolute w-1 h-[1px] bg-gradient-to-r from-transparent via-white to-transparent"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 50}%`,
            }}
            animate={{
              x: [0, 200],
              y: [0, 100],
              opacity: [0, 1, 0],
            }}
            transition={{
              duration: 1,
              repeat: Infinity,
              delay: i * 3 + Math.random() * 5,
              ease: "easeOut"
            }}
          />
        ))}
      </div>

      <div className="relative z-10 min-h-screen flex items-center justify-center p-4">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="w-full max-w-md"
        >
          <div className="bg-card/95 backdrop-blur-md rounded-2xl overflow-hidden shadow-2xl">
            {/* Scenic header illustration */}
            <div className={`relative h-64 bg-gradient-to-b ${getSceneGradient()} overflow-hidden transition-all duration-1000`}>
              {/* Sun/Moon */}
              <motion.div
                className={`absolute top-8 right-12 ${celestialBody.size} bg-gradient-to-br ${celestialBody.gradient} rounded-full transition-all duration-1000 ${
                  timeOfDay === 'night' ? 'shadow-lg shadow-gray-400/30' : 'shadow-xl shadow-yellow-400/40'
                }`}
                animate={{
                  y: [0, 10, 0],
                }}
                transition={{
                  duration: 4,
                  repeat: Infinity,
                  ease: "easeInOut"
                }}
              />
              
              {/* Moon craters (only at night) */}
              {timeOfDay === 'night' && (
                <>
                  <div className="absolute top-10 right-14 w-2 h-2 bg-gray-500/30 rounded-full" />
                  <div className="absolute top-12 right-16 w-3 h-3 bg-gray-500/20 rounded-full" />
                  <div className="absolute top-14 right-12 w-2 h-2 bg-gray-500/25 rounded-full" />
                </>
              )}
              
              {/* Mountains SVG */}
              <svg className="absolute bottom-0 w-full" viewBox="0 0 400 150" preserveAspectRatio="none">
                {/* Back mountain */}
                <motion.path
                  d="M0,150 L100,40 L200,80 L400,150 Z"
                  fill="rgba(99, 102, 241, 0.3)"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 1, delay: 0.2 }}
                />
                {/* Middle mountain */}
                <motion.path
                  d="M0,150 L150,50 L250,90 L400,150 Z"
                  fill="rgba(139, 92, 246, 0.5)"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 1, delay: 0.4 }}
                />
                {/* Front mountain */}
                <motion.path
                  d="M0,150 L80,70 L180,100 L300,60 L400,150 Z"
                  fill="rgba(168, 85, 247, 0.7)"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 1, delay: 0.6 }}
                />
              </svg>
            </div>

            {/* Form section */}
            <div className="p-8 space-y-6">
              <motion.h1 
                className="text-3xl font-bold text-center text-white"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.3 }}
              >
                Echo
              </motion.h1>

              <motion.div 
                className="space-y-4"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.5 }}
              >
                {/* Sign In Button */}
                <motion.button
                  onClick={() => setShowSigninModal(true)}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="w-full py-3 px-4 bg-primary/20 hover:bg-primary/30 border border-primary/30 text-white rounded-lg font-medium transition-all duration-200"
                >
                  Sign In
                </motion.button>

                {/* Create Account Button */}
                <motion.button
                  onClick={() => setShowSignupModal(true)}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="w-full py-3 px-4 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white rounded-lg font-medium transition-all duration-200 shadow-lg"
                >
                  Create Account
                </motion.button>
              </motion.div>

              <motion.p 
                className="text-center text-xs text-gray-400 mt-6"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.7 }}
              >
                100% Local, 100% Private, 100% Yours
              </motion.p>
            </div>
          </div>
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