import { useState, useEffect } from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { Slider } from '@/components/ui/slider'
import { useToast } from '@/components/ui/use-toast'
import { api } from '@/lib/api'
import { Keyboard, Globe, Mic, Settings2, Loader2, CheckCircle2, XCircle } from 'lucide-react'

function SettingsPage() {
  const { toast } = useToast()
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  
  // Hotkey settings
  const [hotkey, setHotkey] = useState('F8')
  const [isRecordingHotkey, setIsRecordingHotkey] = useState(false)
  
  // Ollama settings
  const [ollamaHost, setOllamaHost] = useState('localhost')
  const [ollamaPort, setOllamaPort] = useState('11434')
  const [ollamaModels, setOllamaModels] = useState<string[]>([])
  const [selectedModel, setSelectedModel] = useState('mistral:instruct')
  const [ollamaConnected, setOllamaConnected] = useState<boolean | null>(null)
  const [testingOllama, setTestingOllama] = useState(false)
  const [ollamaTemperature, setOllamaTemperature] = useState('0.7')
  const [ollamaContextWindow, setOllamaContextWindow] = useState('4096')
  
  // TTS settings
  const [ttsEngine, setTtsEngine] = useState('kokoro')
  const [ttsVoice, setTtsVoice] = useState('default')
  const [ttsSpeed, setTtsSpeed] = useState('1.0')
  const [ttsPitch, setTtsPitch] = useState('1.0')
  const [ttsVolume, setTtsVolume] = useState('1.0')
  
  // General settings
  const [autoSave, setAutoSave] = useState(true)
  const [autoSaveInterval, setAutoSaveInterval] = useState('30')
  const [theme, setTheme] = useState('system')

  // Load preferences on mount
  useEffect(() => {
    loadPreferences()
  }, [])

  const loadPreferences = async () => {
    setLoading(true)
    try {
      const response = await api.getPreferences()
      if (response.success && response.data) {
        const prefs = response.data.preferences
        
        // Map preferences to state
        prefs.forEach(pref => {
          switch (pref.key) {
            case 'hotkey':
              setHotkey(pref.typed_value || 'F8')
              break
            case 'ollama_host':
              setOllamaHost(pref.typed_value || 'localhost')
              break
            case 'ollama_port':
              setOllamaPort(String(pref.typed_value || '11434'))
              break
            case 'ollama_model':
              setSelectedModel(pref.typed_value || 'mistral:instruct')
              break
            case 'ollama_temperature':
              setOllamaTemperature(String(pref.typed_value || '0.7'))
              break
            case 'ollama_context_window':
              setOllamaContextWindow(String(pref.typed_value || '4096'))
              break
            case 'tts_engine':
              setTtsEngine(pref.typed_value || 'kokoro')
              break
            case 'tts_voice':
              setTtsVoice(pref.typed_value || 'default')
              break
            case 'tts_speed':
              setTtsSpeed(String(pref.typed_value || '1.0'))
              break
            case 'tts_pitch':
              setTtsPitch(String(pref.typed_value || '1.0'))
              break
            case 'tts_volume':
              setTtsVolume(String(pref.typed_value || '1.0'))
              break
            case 'auto_save':
              setAutoSave(pref.typed_value !== false)
              break
            case 'auto_save_interval':
              setAutoSaveInterval(String(pref.typed_value || '30'))
              break
            case 'theme':
              setTheme(pref.typed_value || 'system')
              break
          }
        })
      }
      
      // Load Ollama models
      await loadOllamaModels()
    } catch (error) {
      console.error('Failed to load preferences:', error)
      toast({
        title: 'Error',
        description: 'Failed to load settings',
        variant: 'destructive'
      })
    } finally {
      setLoading(false)
    }
  }

  const loadOllamaModels = async () => {
    try {
      const response = await api.getOllamaModels()
      if (response.success && response.data) {
        const models = response.data.data?.models || []
        setOllamaModels(models.map((m: any) => m.name))
        setOllamaConnected(true)
      } else {
        setOllamaConnected(false)
      }
    } catch (error) {
      console.error('Failed to load Ollama models:', error)
      setOllamaConnected(false)
    }
  }

  const savePreferences = async (preferences: Array<{ key: string; value: any; value_type: string }>) => {
    setSaving(true)
    try {
      const response = await api.request('/preferences/bulk', {
        method: 'POST',
        body: JSON.stringify({ preferences })
      })
      
      if (response.success) {
        toast({
          title: 'Settings saved',
          description: 'Your preferences have been updated'
        })
        return true
      } else {
        throw new Error(response.error || 'Failed to save preferences')
      }
    } catch (error) {
      console.error('Failed to save preferences:', error)
      toast({
        title: 'Error',
        description: 'Failed to save settings',
        variant: 'destructive'
      })
      return false
    } finally {
      setSaving(false)
    }
  }

  const handleSaveHotkey = async () => {
    const preferences = [
      { key: 'hotkey', value: hotkey, value_type: 'string' }
    ]
    await savePreferences(preferences)
  }

  const handleSaveOllama = async () => {
    const preferences = [
      { key: 'ollama_host', value: ollamaHost, value_type: 'string' },
      { key: 'ollama_port', value: parseInt(ollamaPort), value_type: 'int' },
      { key: 'ollama_model', value: selectedModel, value_type: 'string' },
      { key: 'ollama_temperature', value: parseFloat(ollamaTemperature), value_type: 'float' },
      { key: 'ollama_context_window', value: parseInt(ollamaContextWindow), value_type: 'int' }
    ]
    await savePreferences(preferences)
  }

  const handleSaveTTS = async () => {
    const preferences = [
      { key: 'tts_engine', value: ttsEngine, value_type: 'string' },
      { key: 'tts_voice', value: ttsVoice, value_type: 'string' },
      { key: 'tts_speed', value: parseFloat(ttsSpeed), value_type: 'float' },
      { key: 'tts_pitch', value: parseFloat(ttsPitch), value_type: 'float' },
      { key: 'tts_volume', value: parseFloat(ttsVolume), value_type: 'float' }
    ]
    await savePreferences(preferences)
  }

  const handleSaveGeneral = async () => {
    const preferences = [
      { key: 'auto_save', value: autoSave, value_type: 'bool' },
      { key: 'auto_save_interval', value: parseInt(autoSaveInterval), value_type: 'int' },
      { key: 'theme', value: theme, value_type: 'string' }
    ]
    await savePreferences(preferences)
  }

  const testOllamaConnection = async () => {
    setTestingOllama(true)
    try {
      toast({
        title: 'Testing connection...',
        description: 'Connecting to Ollama service'
      })
      
      // Test connection using saved settings (not current form values)
      const response = await api.testOllamaConnection()
      
      if (response.success && response.data?.data?.service_ready) {
        setOllamaConnected(true)
        toast({
          title: 'Connection successful',
          description: response.data?.message || 'Ollama is connected and ready'
        })
        // Reload models
        await loadOllamaModels()
      } else {
        setOllamaConnected(false)
        toast({
          title: 'Connection failed',
          description: response.error || 'Unable to connect to Ollama',
          variant: 'destructive'
        })
      }
    } catch (error) {
      setOllamaConnected(false)
      toast({
        title: 'Connection failed',
        description: 'Unable to connect to Ollama',
        variant: 'destructive'
      })
    } finally {
      setTestingOllama(false)
    }
  }

  const recordHotkey = () => {
    setIsRecordingHotkey(true)
    
    const handleKeyDown = (e: KeyboardEvent) => {
      e.preventDefault()
      const key = e.key.toUpperCase()
      const modifiers = []
      
      if (e.ctrlKey) modifiers.push('Ctrl')
      if (e.altKey) modifiers.push('Alt')
      if (e.shiftKey) modifiers.push('Shift')
      
      let hotkeyString = ''
      if (modifiers.length > 0) {
        hotkeyString = modifiers.join('+') + '+' + key
      } else if (key.startsWith('F') && !isNaN(parseInt(key.substring(1)))) {
        hotkeyString = key
      } else {
        hotkeyString = modifiers.length > 0 ? modifiers.join('+') + '+' + key : key
      }
      
      setHotkey(hotkeyString)
      setIsRecordingHotkey(false)
      document.removeEventListener('keydown', handleKeyDown)
    }
    
    document.addEventListener('keydown', handleKeyDown)
  }

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto p-8">
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </div>
    )
  }

  return (
    <div className="h-screen flex flex-col p-4 md:p-6 overflow-hidden">
      <div className="max-w-5xl mx-auto w-full flex flex-col flex-1">
        {/* Header */}
        <div className="mb-4">
          <h2 className="text-2xl font-bold text-white mb-1">Settings</h2>
          <p className="text-gray-400 text-sm">
            Configure your Echo journal preferences
          </p>
        </div>

        <Tabs defaultValue="general" className="flex-1 flex flex-col overflow-hidden">
          <TabsList className="grid w-full max-w-md grid-cols-4 mb-4 bg-card/50 backdrop-blur-sm border border-border/50 flex-shrink-0">
            <TabsTrigger value="general" className="flex items-center gap-2 data-[state=active]:bg-primary/10 data-[state=active]:text-primary">
              <Settings2 className="h-4 w-4" />
              <span className="hidden sm:inline">General</span>
            </TabsTrigger>
            <TabsTrigger value="hotkey" className="flex items-center gap-2 data-[state=active]:bg-primary/10 data-[state=active]:text-primary">
              <Keyboard className="h-4 w-4" />
              <span className="hidden sm:inline">Hotkey</span>
            </TabsTrigger>
            <TabsTrigger value="ollama" className="flex items-center gap-2 data-[state=active]:bg-primary/10 data-[state=active]:text-primary">
              <Globe className="h-4 w-4" />
              <span className="hidden sm:inline">Ollama</span>
            </TabsTrigger>
            <TabsTrigger value="tts" className="flex items-center gap-2 data-[state=active]:bg-primary/10 data-[state=active]:text-primary">
              <Mic className="h-4 w-4" />
              <span className="hidden sm:inline">Voice</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="general" className="flex-1 overflow-hidden">
            <Card className="bg-card/50 backdrop-blur-sm border-border/50 h-full flex flex-col overflow-hidden">
              <CardHeader className="pb-2 flex-shrink-0">
                <div className="flex items-center gap-2">
                  <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center flex-shrink-0">
                    <Settings2 className="h-4 w-4 text-white" />
                  </div>
                  <div className="min-w-0">
                    <CardTitle className="text-lg text-white">General Settings</CardTitle>
                    <CardDescription className="text-gray-400 text-sm">
                      Configure general application preferences
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="flex-1 overflow-y-auto space-y-4 p-4">
                {/* Auto-save Setting */}
                <div className="bg-muted/10 rounded-lg p-4 border border-border/50">
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <Label htmlFor="auto-save" className="text-white font-medium">Auto-save entries</Label>
                      <p className="text-sm text-gray-400 mt-1">
                        Automatically save entries while typing
                      </p>
                    </div>
                    <Switch
                      id="auto-save"
                      checked={autoSave}
                      onCheckedChange={setAutoSave}
                      className="data-[state=checked]:bg-primary"
                    />
                  </div>
                  
                  {autoSave && (
                    <div className="mt-4 space-y-2">
                      <Label htmlFor="auto-save-interval" className="text-white font-medium">Auto-save interval</Label>
                      <div className="flex items-center gap-3">
                        <Input
                          id="auto-save-interval"
                          type="number"
                          min="10"
                          max="300"
                          value={autoSaveInterval}
                          onChange={(e) => setAutoSaveInterval(e.target.value)}
                          className="w-24 bg-background/50 border-border text-white placeholder:text-gray-500"
                        />
                        <span className="text-sm text-gray-400">seconds</span>
                      </div>
                    </div>
                  )}
                </div>

                {/* Theme Setting */}
                <div className="bg-muted/10 rounded-lg p-4 border border-border/50">
                  <Label htmlFor="theme" className="text-white font-medium mb-3 block">Theme</Label>
                  <Select value={theme} onValueChange={setTheme}>
                    <SelectTrigger className="w-full max-w-xs bg-background/50 border-border text-white hover:bg-muted/50">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-background border-border">
                      <SelectItem value="light" className="text-white hover:bg-muted/50 focus:bg-muted/50">Light</SelectItem>
                      <SelectItem value="dark" className="text-white hover:bg-muted/50 focus:bg-muted/50">Dark</SelectItem>
                      <SelectItem value="system" className="text-white hover:bg-muted/50 focus:bg-muted/50">System</SelectItem>
                    </SelectContent>
                  </Select>
                  <p className="text-sm text-gray-400 mt-2">
                    Choose your preferred interface theme
                  </p>
                </div>

                {/* Save Button */}
                <div className="flex justify-end pt-2">
                  <button 
                    onClick={handleSaveGeneral} 
                    disabled={saving}
                    className="relative overflow-hidden group px-5 py-2 rounded-lg font-medium shadow-lg hover:shadow-xl hover:scale-[1.02] transition-all duration-300 cursor-pointer inline-flex items-center justify-center bg-primary/10 border border-primary/20 text-primary hover:bg-primary/20 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <div className="absolute inset-0 bg-gradient-to-r from-primary/10 to-secondary/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                    <span className="relative z-10 flex items-center font-medium">
                      {saving ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Saving...
                        </>
                      ) : (
                        'Save Settings'
                      )}
                    </span>
                  </button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="hotkey" className="flex-1 overflow-hidden">
            <Card className="bg-card/50 backdrop-blur-sm border-border/50 h-full flex flex-col overflow-hidden">
              <CardHeader className="pb-2 flex-shrink-0">
                <div className="flex items-center gap-2">
                  <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center flex-shrink-0">
                    <Keyboard className="h-4 w-4 text-white" />
                  </div>
                  <div className="min-w-0">
                    <CardTitle className="text-lg text-white">Hotkey Configuration</CardTitle>
                    <CardDescription className="text-gray-400 text-sm">
                      Configure the global hotkey for voice recording
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="flex-1 overflow-y-auto space-y-4 p-4">
                {/* Hotkey Setting */}
                <div className="bg-muted/10 rounded-lg p-4 border border-border/50">
                  <Label htmlFor="hotkey" className="text-white font-medium mb-3 block">Recording Hotkey</Label>
                  <div className="flex gap-3 mb-3">
                    <Input
                      id="hotkey"
                      value={hotkey}
                      readOnly
                      className="flex-1 font-mono bg-background/50 border-border text-white placeholder:text-gray-500"
                      placeholder="Press Change to set hotkey"
                    />
                    <button
                      onClick={recordHotkey}
                      disabled={isRecordingHotkey}
                      className={`relative overflow-hidden group px-4 py-2 rounded-lg font-medium shadow-lg hover:shadow-xl hover:scale-[1.02] transition-all duration-300 cursor-pointer inline-flex items-center justify-center w-32 ${
                        isRecordingHotkey
                          ? 'bg-red-500/20 border border-red-500/30 text-red-500 animate-pulse'
                          : 'bg-primary/10 border border-primary/20 text-primary hover:bg-primary/20'
                      }`}
                    >
                      <span className="relative z-10 text-center font-medium">
                        {isRecordingHotkey ? 'Press any key...' : 'Change'}
                      </span>
                    </button>
                  </div>
                  <p className="text-sm text-gray-400">
                    Press and hold this key to start recording your voice
                  </p>
                </div>

                {/* Save Button */}
                <div className="flex justify-end pt-2">
                  <button 
                    onClick={handleSaveHotkey} 
                    disabled={saving}
                    className="relative overflow-hidden group px-5 py-2 rounded-lg font-medium shadow-lg hover:shadow-xl hover:scale-[1.02] transition-all duration-300 cursor-pointer inline-flex items-center justify-center bg-primary/10 border border-primary/20 text-primary hover:bg-primary/20 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <div className="absolute inset-0 bg-gradient-to-r from-primary/10 to-secondary/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                    <span className="relative z-10 flex items-center font-medium">
                      {saving ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Saving...
                        </>
                      ) : (
                        'Save Settings'
                      )}
                    </span>
                  </button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="ollama" className="flex-1 overflow-hidden">
            <Card className="bg-card/50 backdrop-blur-sm border-border/50 h-full flex flex-col overflow-hidden">
              <CardHeader className="pb-2 flex-shrink-0">
                <div className="flex items-center gap-2">
                  <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-orange-500 to-red-600 flex items-center justify-center flex-shrink-0">
                    <Globe className="h-4 w-4 text-white" />
                  </div>
                  <div className="min-w-0">
                    <CardTitle className="text-lg text-white">Ollama Configuration</CardTitle>
                    <CardDescription className="text-gray-400 text-sm">
                      Configure connection to your local Ollama instance
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="flex-1 overflow-y-auto space-y-4 p-4">
                {/* Connection Settings */}
                <div className="bg-muted/10 rounded-lg p-3 border border-border/50">
                  <h3 className="text-white font-medium mb-2 text-sm">Connection</h3>
                  <div className="grid grid-cols-2 gap-3 mb-3">
                    <div className="space-y-1">
                      <Label htmlFor="ollama-host" className="text-white font-medium text-sm">Host</Label>
                      <Input
                        id="ollama-host"
                        value={ollamaHost}
                        onChange={(e) => setOllamaHost(e.target.value)}
                        placeholder="localhost"
                        className="bg-background/50 border-border text-white placeholder:text-gray-500 h-9"
                      />
                    </div>
                    <div className="space-y-1">
                      <Label htmlFor="ollama-port" className="text-white font-medium text-sm">Port</Label>
                      <Input
                        id="ollama-port"
                        type="number"
                        value={ollamaPort}
                        onChange={(e) => setOllamaPort(e.target.value)}
                        placeholder="11434"
                        className="bg-background/50 border-border text-white placeholder:text-gray-500 h-9"
                      />
                    </div>
                  </div>

                  {/* Test Connection */}
                  <div className="flex items-center gap-3">
                    <button
                      onClick={testOllamaConnection}
                      disabled={testingOllama}
                      className="relative overflow-hidden group px-3 py-1.5 rounded-md font-medium shadow hover:shadow-lg hover:scale-[1.02] transition-all duration-300 cursor-pointer inline-flex items-center justify-center bg-primary/10 border border-primary/20 text-primary hover:bg-primary/20 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                    >
                      <div className="absolute inset-0 bg-gradient-to-r from-primary/10 to-secondary/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                      <span className="relative z-10 flex items-center font-medium">
                        {testingOllama ? (
                          <>
                            <Loader2 className="mr-2 h-3 w-3 animate-spin" />
                            Testing...
                          </>
                        ) : (
                          'Test Connection'
                        )}
                      </span>
                    </button>
                    {ollamaConnected !== null && (
                      <div className="flex items-center gap-2">
                        {ollamaConnected ? (
                          <>
                            <CheckCircle2 className="h-4 w-4 text-green-500" />
                            <span className="text-sm text-green-500 font-medium">Connected</span>
                          </>
                        ) : (
                          <>
                            <XCircle className="h-4 w-4 text-red-500" />
                            <span className="text-sm text-red-500 font-medium">Not connected</span>
                          </>
                        )}
                      </div>
                    )}
                  </div>
                </div>

                {/* Model Configuration */}
                {ollamaConnected && ollamaModels.length > 0 && (
                  <div className="bg-muted/10 rounded-lg p-3 border border-border/50">
                    <h3 className="text-white font-medium mb-2 text-sm">Model Configuration</h3>
                    
                    {/* Default Model */}
                    <div className="space-y-1 mb-3">
                      <Label htmlFor="ollama-model" className="text-white font-medium text-sm">Default Model</Label>
                      <Select value={selectedModel} onValueChange={setSelectedModel}>
                        <SelectTrigger className="bg-background/50 border-border text-white hover:bg-muted/50 h-9">
                          <SelectValue placeholder="Select a model" />
                        </SelectTrigger>
                        <SelectContent className="bg-background border-border">
                          {ollamaModels.map((model) => (
                            <SelectItem key={model} value={model} className="text-white hover:bg-muted/50 focus:bg-muted/50">
                              {model}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <p className="text-sm text-gray-400">
                        Model used for processing journal entries
                      </p>
                    </div>

                    {/* Model Parameters */}
                    <div className="grid grid-cols-2 gap-3">
                      <div className="space-y-1">
                        <Label htmlFor="ollama-temperature" className="text-white font-medium text-sm">Temperature</Label>
                        <div className="flex items-center gap-2">
                          <Slider
                            id="ollama-temperature"
                            min={0}
                            max={1}
                            step={0.1}
                            value={[parseFloat(ollamaTemperature)]}
                            onValueChange={(value) => setOllamaTemperature(value[0].toString())}
                            className="flex-1 [&>*:first-child]:bg-muted/30 [&>*:first-child]:border-border/50"
                          />
                          <span className="w-10 text-sm text-white font-mono bg-background/50 px-1.5 py-0.5 rounded">
                            {ollamaTemperature}
                          </span>
                        </div>
                        <p className="text-sm text-gray-400">
                          0 = focused, 1 = creative
                        </p>
                      </div>
                      
                      <div className="space-y-1">
                        <Label htmlFor="ollama-context" className="text-white font-medium text-sm">Context Window</Label>
                        <Select value={ollamaContextWindow} onValueChange={setOllamaContextWindow}>
                          <SelectTrigger className="bg-background/50 border-border text-white hover:bg-muted/50 h-9">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent className="bg-background border-border">
                            <SelectItem value="2048" className="text-white hover:bg-muted/50 focus:bg-muted/50">2048 tokens</SelectItem>
                            <SelectItem value="4096" className="text-white hover:bg-muted/50 focus:bg-muted/50">4096 tokens</SelectItem>
                            <SelectItem value="8192" className="text-white hover:bg-muted/50 focus:bg-muted/50">8192 tokens</SelectItem>
                            <SelectItem value="16384" className="text-white hover:bg-muted/50 focus:bg-muted/50">16384 tokens</SelectItem>
                          </SelectContent>
                        </Select>
                        <p className="text-sm text-gray-400">
                          Max conversation length
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Save Button */}
                <div className="flex justify-end pt-2">
                  <button 
                    onClick={handleSaveOllama} 
                    disabled={saving}
                    className="relative overflow-hidden group px-5 py-2 rounded-lg font-medium shadow-lg hover:shadow-xl hover:scale-[1.02] transition-all duration-300 cursor-pointer inline-flex items-center justify-center bg-primary/10 border border-primary/20 text-primary hover:bg-primary/20 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <div className="absolute inset-0 bg-gradient-to-r from-primary/10 to-secondary/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                    <span className="relative z-10 flex items-center font-medium">
                      {saving ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Saving...
                        </>
                      ) : (
                        'Save Settings'
                      )}
                    </span>
                  </button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="tts" className="flex-1">
            <Card className="bg-card/50 backdrop-blur-sm border-border/50">
              <CardHeader className="pb-4">
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-500 to-pink-600 flex items-center justify-center">
                    <Mic className="h-5 w-5 text-white" />
                  </div>
                  <div>
                    <CardTitle className="text-xl text-white">Text-to-Speech Configuration</CardTitle>
                    <CardDescription className="text-gray-400 text-sm">
                      Configure voice output settings (Kokoro TTS - Coming Soon)
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-8">
                {/* Coming Soon Notice */}
                <div className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 rounded-lg p-4 border border-purple-500/20">
                  <div className="flex items-center gap-3 mb-2">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center">
                      <Mic className="h-4 w-4 text-white" />
                    </div>
                    <h3 className="text-white font-medium">Coming Soon</h3>
                  </div>
                  <p className="text-sm text-gray-400">
                    Text-to-Speech integration with Kokoro TTS is coming soon. These settings will be used for the "Talk to Your Diary" feature.
                  </p>
                </div>

                {/* TTS Engine Settings */}
                <div className="bg-muted/10 rounded-lg p-4 border border-border/50 opacity-60">
                  <h3 className="text-white font-medium mb-4">Engine Configuration</h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                    <div className="space-y-2">
                      <Label htmlFor="tts-engine" className="text-white font-medium">TTS Engine</Label>
                      <Select value={ttsEngine} onValueChange={setTtsEngine} disabled>
                        <SelectTrigger className="bg-background/50 border-border text-white hover:bg-muted/50">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="bg-background border-border">
                          <SelectItem value="kokoro" className="text-white hover:bg-muted/50 focus:bg-muted/50">Kokoro TTS</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="tts-voice" className="text-white font-medium">Voice</Label>
                      <Select value={ttsVoice} onValueChange={setTtsVoice} disabled>
                        <SelectTrigger className="bg-background/50 border-border text-white hover:bg-muted/50">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="bg-background border-border">
                          <SelectItem value="default" className="text-white hover:bg-muted/50 focus:bg-muted/50">Default Voice</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  {/* Voice Parameters */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="space-y-3">
                      <Label htmlFor="tts-speed" className="text-white font-medium">Speed</Label>
                      <div className="flex items-center gap-3">
                        <Input
                          id="tts-speed"
                          type="range"
                          min="0.5"
                          max="2"
                          step="0.1"
                          value={ttsSpeed}
                          onChange={(e) => setTtsSpeed(e.target.value)}
                          disabled
                          className="flex-1 bg-background/50 border-border"
                        />
                        <span className="w-12 text-sm text-white font-mono bg-background/50 px-2 py-1 rounded">
                          {ttsSpeed}x
                        </span>
                      </div>
                    </div>
                    
                    <div className="space-y-3">
                      <Label htmlFor="tts-pitch" className="text-white font-medium">Pitch</Label>
                      <div className="flex items-center gap-3">
                        <Input
                          id="tts-pitch"
                          type="range"
                          min="0.5"
                          max="2"
                          step="0.1"
                          value={ttsPitch}
                          onChange={(e) => setTtsPitch(e.target.value)}
                          disabled
                          className="flex-1 bg-background/50 border-border"
                        />
                        <span className="w-12 text-sm text-white font-mono bg-background/50 px-2 py-1 rounded">
                          {ttsPitch}
                        </span>
                      </div>
                    </div>
                    
                    <div className="space-y-3">
                      <Label htmlFor="tts-volume" className="text-white font-medium">Volume</Label>
                      <div className="flex items-center gap-3">
                        <Input
                          id="tts-volume"
                          type="range"
                          min="0"
                          max="1"
                          step="0.1"
                          value={ttsVolume}
                          onChange={(e) => setTtsVolume(e.target.value)}
                          disabled
                          className="flex-1 bg-background/50 border-border"
                        />
                        <span className="w-12 text-sm text-white font-mono bg-background/50 px-2 py-1 rounded">
                          {Math.round(parseFloat(ttsVolume) * 100)}%
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Disabled Save Button */}
                <div className="flex justify-end pt-4">
                  <button 
                    onClick={handleSaveTTS} 
                    disabled={true}
                    className="relative overflow-hidden group px-6 py-3 rounded-lg font-medium shadow-lg transition-all duration-300 cursor-not-allowed inline-flex items-center justify-center bg-gray-500/10 border border-gray-500/20 text-gray-500 disabled:opacity-50"
                  >
                    <span className="relative z-10 flex items-center font-medium">
                      Coming Soon
                    </span>
                  </button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}

export default SettingsPage