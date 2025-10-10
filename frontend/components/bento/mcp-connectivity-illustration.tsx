import type React from "react"
import { Search } from "lucide-react"

interface McpConnectivityIllustrationProps {
  className?: string
}

const McpConnectivityIllustration: React.FC<McpConnectivityIllustrationProps> = ({ className = "" }) => {
  const integrations = [
    { name: "GitHub", icon: "/images/mcp-integrations/github.svg", installed: true },
    { name: "GitLab", icon: "/images/mcp-integrations/gitlab.svg" },
    { name: "Bitbucket", icon: "/images/mcp-integrations/bitbucket.svg", installed: true },
    { name: "Slack", icon: "/images/mcp-integrations/slack.svg" },
    { name: "Jira", icon: "/images/mcp-integrations/jira.svg", installed: true },
    { name: "OSV.dev", icon: "/images/mcp-integrations/osv.svg" },
  ]

  return (
    <div
      className={`w-full h-full flex items-center justify-center p-4 relative ${className}`}
      role="img"
      aria-label="MCP Connectivity component showcasing installed integrations list"
    >
      {/* Main Message Box */}
      <div
        style={{
          position: "absolute",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, calc(-50% + 24px))",
          width: "345px",
          height: "277px",
          background: "linear-gradient(180deg, hsl(var(--background)) 0%, transparent 100%)",
          backdropFilter: "blur(16px)",
          borderRadius: "9.628px",
          border: "0.802px solid hsl(var(--border))",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            height: "100%",
            width: "100%",
          }}
        >
          {/* Search Header */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "12.837px",
              padding: "8.826px 12.837px",
              borderBottom: "0.802px solid hsl(var(--border))",
              width: "100%",
              boxSizing: "border-box",
            }}
          >
            <div
              style={{
                width: "14.442px",
                height: "14.442px",
                position: "relative",
                flexShrink: 0,
              }}
            >
              <Search className="w-full h-full text-muted-foreground" />
            </div>
            <span
              style={{
                fontFamily: "'Geist', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
                fontSize: "12.837px",
                lineHeight: "19.256px",
                color: "hsl(var(--muted-foreground))",
                fontWeight: 400,
                whiteSpace: "nowrap",
              }}
            >
              Search for integrations
            </span>
          </div>
          {/* Integration List */}
          {integrations.map((integration, index) => (
            <div
              key={integration.name}
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "8.826px 12.837px",
                borderBottom: index < integrations.length - 1 ? "0.479px solid hsl(var(--border))" : "none",
                width: "100%",
                boxSizing: "border-box",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "12.837px",
                }}
              >
                <div
                  style={{
                    width: "24px",
                    height: "24px",
                    position: "relative",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    flexShrink: 0,
                  }}
                >
                  <img
                    src={integration.icon || "/placeholder.svg"}
                    alt={integration.name}
                    className="w-full h-full object-contain opacity-70 grayscale" // Apply opacity and grayscale
                  />
                </div>
                <span
                  style={{
                    fontFamily: "'Geist', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
                    fontSize: "12.837px",
                    lineHeight: "19.256px",
                    color: "hsl(var(--muted-foreground))",
                    fontWeight: 400,
                    whiteSpace: "nowrap",
                  }}
                >
                  {integration.name}
                </span>
              </div>
              {integration.installed && (
                <div
                  style={{
                    background: "hsl(var(--primary) / 0.08)",
                    padding: "1.318px 5.272px",
                    borderRadius: "3.295px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                >
                  <span
                    style={{
                      fontFamily: "'Geist', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
                      fontSize: "9.583px",
                      lineHeight: "15.333px",
                      color: "hsl(var(--primary))",
                      fontWeight: 500,
                      whiteSpace: "nowrap",
                    }}
                  >
                    Installed
                  </span>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default McpConnectivityIllustration
