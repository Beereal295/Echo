function ViewEntriesPage() {
  return (
    <div className="flex h-full">
      {/* Entry List - Left Side */}
      <div className="w-96 border-r overflow-auto bg-muted/20">
        <div className="p-4 border-b bg-background sticky top-0 z-10">
          <h2 className="text-xl font-bold">Your Entries</h2>
        </div>
        <div className="p-4">
          <p className="text-muted-foreground text-center">No entries yet</p>
        </div>
      </div>

      {/* Entry Detail - Right Side */}
      <div className="flex-1 overflow-auto">
        <div className="flex items-center justify-center h-full text-muted-foreground">
          Select an entry to view details
        </div>
      </div>
    </div>
  )
}

export default ViewEntriesPage