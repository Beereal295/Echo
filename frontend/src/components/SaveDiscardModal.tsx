import { Button } from '@/components/ui/button'
import { Save, Trash2 } from 'lucide-react'
import { motion } from 'framer-motion'

interface SaveDiscardModalProps {
  isOpen: boolean
  onClose: () => void
  onSave: () => void
  onDiscard: () => void
  transcription: string
  duration: number
  messageCount: number
}

function SaveDiscardModal({
  isOpen,
  onClose,
  onSave,
  onDiscard,
  transcription,
  duration,
  messageCount
}: SaveDiscardModalProps) {
  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  if (!isOpen) return null

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        className="bg-card/90 backdrop-blur-xl border border-border/50 rounded-2xl shadow-2xl max-w-3xl w-full max-h-[80vh] flex flex-col overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="px-6 pt-6 pb-4 border-b border-border/50">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-green-500 to-teal-600 flex items-center justify-center">
              <Save className="h-4 w-4 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-white mb-1">Save Conversation?</h2>
              <p className="text-sm text-gray-400">
                Review your chat with Echo and decide if you'd like to save it.
              </p>
            </div>
          </div>
        </div>

        <div className="flex-1 flex flex-col gap-4 overflow-hidden">
          {/* Conversation Info */}
          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            <span>Duration: {formatDuration(duration)}</span>
            <span>•</span>
            <span>{messageCount} messages</span>
          </div>

          {/* Transcription Preview */}
          <div className="flex-1 overflow-hidden border rounded-lg">
            <div className="h-full p-4 overflow-y-auto">
              <pre className="text-sm whitespace-pre-wrap font-sans">{transcription}</pre>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3 justify-end">
            <button
              onClick={onDiscard}
              className="relative overflow-hidden group px-6 py-2.5 rounded-lg font-medium transition-all duration-300 cursor-pointer inline-flex items-center justify-center bg-muted/10 border border-muted/20 text-muted-foreground hover:bg-muted/20 gap-2"
            >
              <Trash2 className="h-4 w-4" />
              Discard
            </button>
            <button
              onClick={onSave}
              className="relative overflow-hidden group px-6 py-2.5 rounded-lg font-medium shadow-lg hover:shadow-xl transition-all duration-300 cursor-pointer inline-flex items-center justify-center bg-primary/10 border border-primary/20 text-primary hover:bg-primary/20 gap-2"
            >
              <div className="absolute inset-0 bg-gradient-to-r from-primary/10 to-secondary/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
              <span className="relative z-10 flex items-center">
                <Save className="h-4 w-4 mr-2" />
                Save Conversation
              </span>
            </button>
          </div>
        </div>
      </motion.div>
    </motion.div>
  )
}

export default SaveDiscardModal