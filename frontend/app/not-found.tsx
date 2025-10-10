export default function NotFound() {
  return (
    <div className="min-h-[60vh] flex items-center justify-center px-6">
      <div className="text-center">
        <h1 className="text-foreground text-3xl md:text-5xl font-semibold mb-3">Page not found</h1>
        <p className="text-muted-foreground">The page you are looking for does not exist.</p>
      </div>
    </div>
  )
} 