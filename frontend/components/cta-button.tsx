import { Button } from "@/components/ui/button"

interface CTAButtonProps {
  href: string
  children: React.ReactNode
  className?: string
}

export function CTAButton({ href, children, className = "" }: CTAButtonProps) {
  const isExternal = href.startsWith('http') || href.startsWith('https')
  
  return (
    <Button asChild className={`bg-white text-black hover:bg-gray-100 px-10 py-5 md:px-12 md:py-6 rounded-full font-medium text-lg md:text-xl shadow-lg ${className}`}>
      <a 
        href={href} 
        {...(isExternal && { target: "_blank", rel: "noopener noreferrer" })}
      >
        {children}
      </a>
    </Button>
  )
}