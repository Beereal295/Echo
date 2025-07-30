import { motion } from 'framer-motion'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { FileText, Sparkles, Zap, Pen, BookOpen } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

function HomePage() {
  const navigate = useNavigate()
  
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
    <motion.div 
      className="max-w-6xl mx-auto p-4 md:p-8 min-h-screen flex flex-col justify-center"
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
          className="text-gray-300 text-xl md:text-2xl max-w-2xl mx-auto leading-relaxed"
          variants={itemVariants}
        >
          Express yourself in three different ways with the power of AI
        </motion.p>
        
        {/* Floating elements */}
        <motion.div 
          className="absolute top-20 left-20 text-primary/20"
          animate={{ 
            y: [-10, 10, -10],
            rotate: [0, 5, 0]
          }}
          transition={{ 
            duration: 4,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        >
          <Sparkles className="w-8 h-8" />
        </motion.div>
        
        <motion.div 
          className="absolute top-32 right-32 text-secondary/20"
          animate={{ 
            y: [10, -10, 10],
            rotate: [0, -5, 0]
          }}
          transition={{ 
            duration: 5,
            repeat: Infinity,
            ease: "easeInOut",
            delay: 1
          }}
        >
          <Zap className="w-6 h-6" />
        </motion.div>
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
              onClick={() => navigate('/entries')}
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
            </Card>
          </motion.div>
        ))}
      </motion.div>

      {/* Quick Tips */}
      <motion.div variants={itemVariants}>
        <Card className="bg-muted/30 backdrop-blur-sm border-border/50 relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-r from-primary/5 via-transparent to-accent/5" />
          <CardContent className="pt-8 pb-8 relative">
            <div className="flex items-center justify-center space-x-4 text-center">
              <motion.div
                animate={{ scale: [1, 1.1, 1] }}
                transition={{ duration: 2, repeat: Infinity }}
              >
                <Sparkles className="w-6 h-6 text-primary" />
              </motion.div>
              <p className="text-gray-300 text-lg">
                Click the{' '}
                <span className="font-semibold text-primary">plus button</span>{' '}
                or press{' '}
                <kbd className="px-3 py-1 text-sm bg-muted border border-border rounded-md font-mono text-white">
                  Ctrl+N
                </kbd>{' '}
                to create your first entry
              </p>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </motion.div>
  )
}

export default HomePage