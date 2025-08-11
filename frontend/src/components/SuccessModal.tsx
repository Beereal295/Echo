import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { CheckCircle, X } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface SuccessModalProps {
  isOpen: boolean
  title: string
  message: string
  autoCloseMs?: number
  onClose: () => void
}

function SuccessModal({ isOpen, title, message, autoCloseMs = 3000, onClose }: SuccessModalProps) {
  const [countdown, setCountdown] = useState(autoCloseMs / 1000)

  useEffect(() => {
    if (!isOpen) return

    setCountdown(autoCloseMs / 1000)
    
    const interval = setInterval(() => {
      setCountdown(prev => {
        if (prev <= 1) {
          onClose()
          return 0
        }
        return prev - 1
      })
    }, 1000)

    return () => clearInterval(interval)
  }, [isOpen, autoCloseMs, onClose])

  return (
    <AnimatePresence mode="wait">
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.3, ease: "easeInOut" }}
          className="fixed inset-0 z-[60] flex items-center justify-center bg-black/80 backdrop-blur-md p-4"
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.85, opacity: 0, y: -20 }}
            transition={{ 
              type: "spring", 
              stiffness: 300, 
              damping: 30,
              exit: { duration: 0.25, ease: "easeIn" }
            }}
            className="bg-card border border-border rounded-lg shadow-2xl overflow-hidden max-w-md w-full"
          >
            {/* Header */}
            <div className="px-6 py-4 border-b border-border bg-green-500/5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-green-500/20 flex items-center justify-center">
                    <CheckCircle className="h-4 w-4 text-green-400" />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-white">{title}</h2>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={onClose}
                  className="h-8 w-8 p-0 text-green-300 hover:bg-muted/50 hover:text-white"
                  title="Close"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </div>

            {/* Content */}
            <div className="p-6">
              <p className="text-gray-300 text-sm mb-4">{message}</p>
              
              {/* Auto-close countdown */}
              <div className="flex items-center justify-between">
                <div className="text-xs text-gray-500">
                  Closing in {countdown}s...
                </div>
                <div className="flex gap-2">
                  <Button
                    onClick={onClose}
                    size="sm"
                    className="bg-green-500/10 border border-green-500/20 text-green-400 hover:bg-green-500/20"
                  >
                    Continue
                  </Button>
                </div>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

export default SuccessModal