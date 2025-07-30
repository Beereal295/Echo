import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'

function NewEntryPage() {
  return (
    <div className="max-w-3xl mx-auto p-4 md:p-8">
      <h2 className="text-2xl font-bold mb-6 text-white">New Entry</h2>

      <Card className="p-6">
        <div className="relative">
          <Textarea
            placeholder="Start typing or hold F8 to speak..."
            className="min-h-[300px] resize-none pr-16 text-lg text-white placeholder:text-gray-400 bg-transparent border-border"
          />
        </div>

        <div className="mt-6 flex justify-end">
          <button className="relative overflow-hidden group px-8 py-3 rounded-md font-medium shadow-md hover:shadow-lg hover:scale-[1.02] transition-all duration-300 cursor-pointer inline-flex items-center justify-center bg-primary/10 border border-primary/20 text-primary hover:bg-primary/20">
            {/* Animated background on hover */}
            <div className="absolute inset-0 bg-gradient-to-r from-primary/10 to-secondary/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
            
            {/* Button text */}
            <span className="relative z-10 text-primary font-medium group-hover:text-primary transition-colors duration-300">
              Create All Three Entries
            </span>
          </button>
        </div>
      </Card>
    </div>
  )
}

export default NewEntryPage