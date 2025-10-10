"use client"

import { motion, useReducedMotion } from "framer-motion"
import type { HTMLAttributes, ReactNode } from "react"

interface AnimatedSectionProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode
  delay?: number
}

export function AnimatedSection({ children, className, delay = 0, ...props }: AnimatedSectionProps) {
  const reduceMotion = useReducedMotion()
  const initial = reduceMotion ? { opacity: 0 } : { opacity: 0, y: 16 }
  const animate = reduceMotion ? { opacity: 1 } : { opacity: 1, y: 0 }

  return (
    <motion.div
      initial={initial}
      whileInView={animate}
      viewport={{ once: true, margin: "-50px" }}
      transition={{ duration: 0.35, ease: [0.33, 1, 0.68, 1], delay: reduceMotion ? 0 : delay }}
      className={className}
      {...props}
    >
      {children}
    </motion.div>
  )
}
